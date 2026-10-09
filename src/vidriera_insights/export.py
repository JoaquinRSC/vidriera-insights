"""Export the price estimator as static JSON for the web app.

    python -m vidriera_insights.export [--refresh]

The browser can't run scikit-learn, so the models are evaluated here on a grid of
(year, mileage) per car model and the web page interpolates between grid points.
"""

import argparse
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from . import analysis, model
from .fetch import load_cards, load_new_cars, load_new_price_history

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "vehicle_cards.csv"
NEW_CARS = ROOT / "data" / "new_cars.csv"
PRICE_HISTORY = ROOT / "data" / "new_price_history.csv"
OUT = ROOT / "web" / "data.json"

MIN_LISTINGS = 5  # models with fewer used cars aren't offered in the estimator
KM_STEP = 10_000
MAX_LISTED = 60  # current listings shipped per model, for the "similar cars" list


def mode_or_unknown(values: pd.Series) -> str:
    counts = values.dropna().value_counts()
    return str(counts.index[0]) if len(counts) else "unknown"


def km_grid(mileage: pd.Series) -> list[int]:
    top = mileage.quantile(0.95) if mileage.notna().any() else 150_000
    top = int(np.clip(np.ceil(top * 1.2 / KM_STEP) * KM_STEP, 60_000, 300_000))
    return list(range(0, top + KM_STEP, KM_STEP))


def to_matrix(log_values: np.ndarray, shape: tuple[int, int]) -> list[list[int]]:
    """Log prices back to USD, rounded to 10, as a years x km matrix."""
    return (np.round(np.exp(log_values) / 10) * 10).astype(int).reshape(shape).tolist()


def model_grids(df: pd.DataFrame, models: dict, margin: float, today_year: int) -> list[dict]:
    """Low/mid/high price per (year, km) for every model with enough listings."""
    data = model.prepare(df)
    counts = data.groupby(["brand", "model"]).size()
    entries = []
    for (brand, name), n in counts[counts >= MIN_LISTINGS].items():
        cars = data[(data["brand"] == brand) & (data["model"] == name)]
        years = list(range(int(max(cars["year"].min(), today_year - 20)), int(cars["year"].max()) + 1))
        kms = km_grid(cars["mileage_km"])
        grid = pd.DataFrame([(y, k) for y in years for k in kms], columns=["year", "mileage_km"])
        grid = grid.assign(brand=brand, model=name, age=today_year - grid["year"],
                           fuel=mode_or_unknown(cars["fuel"]), transmission=mode_or_unknown(cars["transmission"]),
                           body_type=mode_or_unknown(cars["body_type"]))
        _, grid = model.collapse_rare(data, grid)
        preds = {key: models[key].predict(grid[model.FEATURES]) for key in ("low", "mid", "high")}
        low = np.minimum(preds["low"], preds["mid"]) - margin
        high = np.maximum(preds["high"], preds["mid"]) + margin
        shape = (len(years), len(kms))

        listed = cars.sort_values("first_seen_at", ascending=False).head(MAX_LISTED)
        entries.append({
            "brand": brand, "model": name, "listings": int(n),
            "fuel": mode_or_unknown(cars["fuel"]),
            "years": years, "km": kms,
            "low": to_matrix(low, shape), "mid": to_matrix(preds["mid"], shape), "high": to_matrix(high, shape),
            "cars": [
                [int(r.year), None if pd.isna(r.mileage_km) else int(r.mileage_km), int(r.price), r.source_name,
                 r.url if isinstance(r.url, str) else None]
                for r in listed.itertuples()
            ],
        })
    return entries


def attach_depreciation(entries: list[dict], df: pd.DataFrame, history: pd.DataFrame,
                        new_cars: pd.DataFrame) -> None:
    """Depreciation figures, 0 km price of each model year, and today's 0 km price."""
    by_model = analysis.model_depreciation(df).set_index(["brand", "model"])
    from_new = analysis.depreciation_from_new(df, history).set_index(["brand", "model"])
    for entry in entries:
        key = (entry["brand"], entry["model"])
        cars = df[(df["brand"] == key[0]) & (df["model"] == key[1])]
        if key in by_model.index:
            row = by_model.loc[key]
            entry["depreciation"] = {k: None if pd.isna(row[k]) else float(row[k])
                                     for k in ("yearly_loss_pct", "loss_per_10k_km_pct", "total_yearly_loss_pct")}
        if key in from_new.index:
            row = from_new.loc[key]
            entry["from_new"] = {k: None if pd.isna(row[k]) else float(row[k])
                                 for k in ("kept_1y_pct", "kept_3y_pct", "kept_5y_pct", "kept_3y_vs_base_pct")}
        by_year = analysis.new_price_by_year(*key, history, cars)
        entry["new_by_year"] = {str(int(r.year)): int(r.new_price) for r in by_year.itertuples()}
        today = analysis.new_price_for(*key, new_cars, cars)
        entry["new_today"] = None if today is None else int(today)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="download fresh data first")
    args = parser.parse_args()

    today = date.today()
    df = analysis.clean(load_cards(CACHE, refresh=args.refresh), today.year)
    new_cars = load_new_cars(NEW_CARS, refresh=args.refresh)
    history = load_new_price_history(PRICE_HISTORY, sorted(new_cars["brand"].unique()), refresh=args.refresh)

    models, margin = model.fit_price_range(df)
    coverage = model.interval_coverage(df).mean()
    cv = model.cross_validate(df).mean()
    entries = model_grids(df, models, margin, today.year)
    attach_depreciation(entries, df, history, new_cars)
    electrified = analysis.powertrain_summary(df).reset_index()

    payload = {
        "generated": today.isoformat(),
        "listings": len(df),
        "dealers": int(df["source_name"].nunique()),
        "new_prices_updated": None if new_cars.empty else new_cars["list_updated"].dropna().iloc[0],
        "new_price_years": [int(history["year"].min()), int(history["year"].max())],
        "quality": {
            "mape_pct": round(float(cv["mape_all_pct"]), 1),
            "interval_coverage_pct": round(float(coverage["calibrated_coverage_pct"]), 1),
            "interval_raw_coverage_pct": round(float(coverage["raw_coverage_pct"]), 1),
        },
        "electrified": electrified.to_dict(orient="records"),
        "models": sorted(entries, key=lambda e: (e["brand"], e["model"])),
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {OUT} ({len(entries)} models, {OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
