"""Pure pandas analyses over the vehicle_cards dataset (no I/O, easy to test)."""

import numpy as np
import pandas as pd

MIN_SAMPLE = 10  # groups smaller than this are too noisy to report


def clean(df: pd.DataFrame, today_year: int) -> pd.DataFrame:
    """Keep active USD listings with a plausible price, year and mileage."""
    out = df[(df["status"] == "active") & (df["currency"] == "USD")].copy()
    out = out.dropna(subset=["price", "year", "brand"])
    out = out[(out["price"].between(1_000, 500_000)) & (out["year"].between(1980, today_year + 1))]
    out.loc[out["mileage_km"] > 1_000_000, "mileage_km"] = np.nan  # typos like 1.500.000 km
    out["age"] = today_year - out["year"]
    out["brand"] = out["brand"].str.strip().str.title()
    # Dealers spell models inconsistently ("JOY", "Joy"): compare on a normalized key.
    out["model"] = out["model"].str.strip().str.title()
    for col in {"fuel", "transmission", "body_type"} & set(out.columns):
        out[col] = out[col].replace({"—": np.nan, "": np.nan})
    return out


def brand_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Listing count and median price/year/mileage per brand, most listed first."""
    summary = df.groupby("brand").agg(
        listings=("id", "count"),
        median_price=("price", "median"),
        median_year=("year", "median"),
        median_km=("mileage_km", "median"),
    )
    return summary[summary["listings"] >= MIN_SAMPLE].sort_values("listings", ascending=False)


def segment_summary(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Median price and age per value of a categorical column (fuel, transmission...)."""
    known = df.dropna(subset=[column])
    summary = known.groupby(column).agg(
        listings=("id", "count"),
        median_price=("price", "median"),
        median_age=("age", "median"),
    )
    return summary[summary["listings"] >= MIN_SAMPLE].sort_values("median_price", ascending=False)


def depreciation_curve(df: pd.DataFrame, max_age: int = 15) -> pd.DataFrame:
    """Median price by age, plus how much value is kept relative to age 0-1."""
    curve = (
        df[df["age"].between(0, max_age)]
        .groupby("age")
        .agg(listings=("id", "count"), median_price=("price", "median"))
    )
    curve = curve[curve["listings"] >= MIN_SAMPLE]
    baseline = curve["median_price"].iloc[:2].mean()
    curve["value_kept_pct"] = (curve["median_price"] / baseline * 100).round(1)
    return curve


def model_depreciation(
    df: pd.DataFrame, min_listings: int = 20, min_years: int = 4, max_age: int = 12
) -> pd.DataFrame:
    """Yearly value loss per model, fitted as log(price) = a + b * age.

    A log-linear fit turns the slope into a constant percentage per year, which is
    how depreciation behaves and lets a USD 8k and a USD 40k model be compared.
    """
    rows = []
    # Very old cars hit a price floor and would flatten every curve, so they're left out.
    recent = df[df["age"].between(0, max_age)].dropna(subset=["model"])
    for (brand, model), group in recent.groupby(["brand", "model"]):
        if len(group) < min_listings or group["age"].nunique() < min_years:
            continue
        slope, _ = np.polyfit(group["age"], np.log(group["price"]), 1)
        rows.append({
            "brand": brand,
            "model": model,
            "listings": len(group),
            "median_price": group["price"].median(),
            "yearly_loss_pct": round((1 - np.exp(slope)) * 100, 1),
        })
    columns = ["brand", "model", "listings", "median_price", "yearly_loss_pct"]
    return pd.DataFrame(rows, columns=columns).sort_values("yearly_loss_pct").reset_index(drop=True)


def mileage_effect(df: pd.DataFrame) -> float:
    """USD lost per extra 10,000 km for cars of the same model and year.

    Prices are demeaned within each (brand, model, year) group, so the slope only
    reflects mileage, not the fact that older cars have both more km and lower prices.
    """
    data = df.dropna(subset=["mileage_km", "model"]).copy()
    keys = ["brand", "model", "year"]
    data = data[data.groupby(keys)["id"].transform("count") >= 3]
    data["price_dev"] = data["price"] - data.groupby(keys)["price"].transform("mean")
    data["km_dev"] = data["mileage_km"] - data.groupby(keys)["mileage_km"].transform("mean")
    slope, _ = np.polyfit(data["km_dev"], data["price_dev"], 1)
    return round(slope * 10_000, 2)


def dealer_pricing(df: pd.DataFrame, anonymize: bool = False) -> pd.DataFrame:
    """How each dealer prices against the market (median % vs. fair price)."""
    priced = df.dropna(subset=["price_vs_fair_pct"])
    table = priced.groupby("source_name").agg(
        listings=("id", "count"),
        median_vs_fair_pct=("price_vs_fair_pct", "median"),
        share_above_fair=("price_vs_fair_pct", lambda s: round((s > 5).mean() * 100, 1)),
    )
    table = table[table["listings"] >= MIN_SAMPLE].sort_values("median_vs_fair_pct")
    if anonymize:
        table.index = [f"Automotora {chr(65 + i)}" for i in range(len(table))]
        table.index.name = "source_name"
    return table


def time_on_market(df: pd.DataFrame) -> pd.DataFrame:
    """Do overpriced cars stay listed longer? Days listed by price bucket."""
    priced = df.dropna(subset=["price_vs_fair_pct"]).copy()
    bins = [-np.inf, -10, -2, 2, 10, np.inf]
    labels = ["<-10%", "-10 a -2%", "±2%", "+2 a +10%", ">+10%"]
    priced["bucket"] = pd.cut(priced["price_vs_fair_pct"], bins=bins, labels=labels)
    return priced.groupby("bucket", observed=True).agg(
        listings=("id", "count"),
        median_days=("days_listed", "median"),
        share_with_price_cut=("price_changes", lambda s: round((s > 0).mean() * 100, 1)),
    )


def market_trend(snapshots: pd.DataFrame) -> pd.DataFrame:
    """Stock size and median price per snapshot date (one row per saved run)."""
    return (
        snapshots.groupby("snapshot_date")
        .agg(listings=("id", "count"), median_price=("price", "median"))
        .sort_index()
    )
