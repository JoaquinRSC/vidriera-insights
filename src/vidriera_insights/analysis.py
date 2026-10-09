"""Pure pandas analyses over the vehicle_cards dataset (no I/O, easy to test)."""

import re

import numpy as np
import pandas as pd

MIN_SAMPLE = 10  # groups smaller than this are too noisy to report

# About a quarter of listings don't state the fuel; EVs and hybrids usually say so in the title.
ELECTRIC_HINTS = re.compile(r"\bel[eé]ctric|\bev\b|\bbev\b|\bseagull\b|\bdolphin\b|\byuan\b|\batto\b|\bleaf\b")
HYBRID_HINTS = re.compile(r"h[ií]brid|\bhybrid\b|\bhev\b|\bphev\b|\bmhev\b|e-power|\bdm-i\b")


def infer_fuel(df: pd.DataFrame) -> pd.Series:
    """Fuel as listed, or Eléctrico/Híbrido when only the title gives it away."""
    text_cols = [c for c in ("title", "version") if c in df.columns]
    if not text_cols:
        return df["fuel"]
    text = df[text_cols].fillna("").agg(" ".join, axis=1).str.lower()
    inferred = pd.Series(np.nan, index=df.index, dtype="object")
    inferred[text.str.contains(HYBRID_HINTS)] = "Híbrido"
    inferred[text.str.contains(ELECTRIC_HINTS)] = "Eléctrico"
    return df["fuel"].fillna(inferred)


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
    if "fuel" in out.columns:
        out["fuel"] = infer_fuel(out)
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
    """Yearly value loss per model, separating age from mileage.

    Two log-linear fits per model:
    - ``log(price) = a + b*age`` gives the *total* yearly loss a buyer sees, which
      mixes getting older with accumulating kilometres;
    - ``log(price) = a + b*age + c*km`` holds mileage fixed, so ``b`` is the loss
      from age alone and ``c`` the loss per extra 10,000 km.
    Logs turn slopes into constant percentages, so a USD 8k and a USD 40k model compare.
    """
    rows = []
    # Very old cars hit a price floor and would flatten every curve, so they're left out.
    recent = df[df["age"].between(0, max_age)].dropna(subset=["model"])
    for (brand, model), group in recent.groupby(["brand", "model"]):
        if len(group) < min_listings or group["age"].nunique() < min_years:
            continue
        total_slope, _ = np.polyfit(group["age"], np.log(group["price"]), 1)
        row = {
            "brand": brand,
            "model": model,
            "listings": len(group),
            "median_price": group["price"].median(),
            "total_yearly_loss_pct": pct_loss(total_slope),
            "yearly_loss_pct": np.nan,
            "loss_per_10k_km_pct": np.nan,
        }
        with_km = group.dropna(subset=["mileage_km"])
        if len(with_km) >= min_listings and with_km["age"].nunique() >= min_years:
            X = np.column_stack([np.ones(len(with_km)), with_km["age"], with_km["mileage_km"] / 10_000])
            (_, age_slope, km_slope), *_ = np.linalg.lstsq(X, np.log(with_km["price"]), rcond=None)
            row["yearly_loss_pct"] = pct_loss(age_slope)
            row["loss_per_10k_km_pct"] = pct_loss(km_slope)
        rows.append(row)
    columns = ["brand", "model", "listings", "median_price", "yearly_loss_pct", "loss_per_10k_km_pct",
               "total_yearly_loss_pct"]
    table = pd.DataFrame(rows, columns=columns)
    return table.sort_values(["yearly_loss_pct", "total_yearly_loss_pct"]).reset_index(drop=True)


def pct_loss(log_slope: float) -> float:
    """Turn a slope on log(price) into the % of value lost per unit."""
    return round((1 - np.exp(log_slope)) * 100, 1)


NEW_ELECTRIC = re.compile(r"\bev\b|\bbev\b|kwh|el[eé]ctric")
NEW_HYBRID = re.compile(r"h[ií]brid|hybrid|\bphev\b|\bhev\b|\bmhev\b|\bdht\b|e-power|\bdm-i\b")
# Words that, right after the model name, mark a different car rather than a trim.
SUB_MODELS = {"plus", "sport", "pro", "cross", "max", "sedan", "sedán", "hatch", "cabrio", "coupé", "coupe"}


def powertrain_of(name: str) -> str:
    name = name.lower()
    if NEW_ELECTRIC.search(name):
        return "Eléctrico"
    if NEW_HYBRID.search(name):
        return "Híbrido"
    return "Combustión"


def new_versions_for(brand: str, model: str, new: pd.DataFrame, used: pd.DataFrame | None = None) -> pd.DataFrame:
    """0 km list entries comparable to the used cars of a model.

    Starts from every version whose name begins with the model ("Onix 1.0 LT",
    "Onix Plus Premier") and, when the used cars are given, drops the versions that
    are really a different car:
    - another powertrain (an EV or plug-in version next to petrol used cars);
    - a sub-model ("Swift Sport") that barely appears among the used listings.
    A sub-model shared by every 0 km version ("GX3 Pro") is just the model's name.
    """
    same_brand = new[new["brand"] == brand]
    pattern = re.compile(rf"^{re.escape(model.lower())}(\s|$)")
    matches = same_brand[same_brand["name"].str.lower().str.match(pattern)].copy()
    if used is None or matches.empty:
        return matches

    rest = matches["name"].str.lower().str.slice(len(model)).str.strip()
    next_word = rest.str.split().str[0].fillna("")
    text_cols = [c for c in ("version", "title") if c in used.columns]
    used_text = used[text_cols].fillna("").agg(" ".join, axis=1).str.lower()
    for word in set(next_word) & SUB_MODELS:
        if (next_word == word).all():
            continue
        if used_text.str.contains(rf"\b{re.escape(word)}\b").mean() < 0.1:
            matches = matches[next_word != word]
            next_word = next_word[next_word != word]

    used_fuel = used["fuel"].mode() if "fuel" in used.columns else pd.Series(dtype="object")
    target = used_fuel.iloc[0] if len(used_fuel) and used_fuel.iloc[0] in ("Eléctrico", "Híbrido") else "Combustión"
    same_powertrain = matches[matches["name"].map(powertrain_of) == target]
    # Some models are now only sold electrified (the new Swift is a mild hybrid):
    # then the remaining versions are still the closest thing to "this model, new".
    return same_powertrain if len(same_powertrain) else matches


def new_price_for(brand: str, model: str, new: pd.DataFrame, used: pd.DataFrame | None = None) -> float | None:
    """Median 0 km list price over the comparable versions of a model."""
    versions = new_versions_for(brand, model, new, used)
    return float(versions["price"].median()) if len(versions) else None


def new_price_by_year(brand: str, model: str, history: pd.DataFrame,
                      used: pd.DataFrame | None = None) -> pd.DataFrame:
    """Median and cheapest comparable 0 km price of a model for each list year."""
    rows = []
    for year, prices in history.groupby("year"):
        versions = new_versions_for(brand, model, prices, used)
        if len(versions):
            rows.append({"year": int(year), "new_price": float(versions["price"].median()),
                         "base_price": float(versions["price"].min()), "versions": len(versions)})
    return pd.DataFrame(rows, columns=["year", "new_price", "base_price", "versions"])


def depreciation_from_new(
    used: pd.DataFrame, history: pd.DataFrame, min_used: int = 10, max_age: int = 7
) -> pd.DataFrame:
    """Value kept vs. what the same model cost new **in its own year**.

    Each used car is compared with the 0 km list price of its model year (Autoblog's
    list as archived at the start of that year), so price changes over time don't
    distort the result. Then ``log(used_price / new_price_that_year) = a + b*age`` is
    fitted per model and read at 1, 3 and 5 years; the free intercept captures the
    first-owner discount. ``max_age`` keeps the comparison within the years the
    archive covers and the current generation.
    """
    rows = []
    recent = used[used["age"].between(0, max_age)].dropna(subset=["model"])
    for (brand, model), group in recent.groupby(["brand", "model"]):
        if len(group) < min_used:
            continue
        by_year = new_price_by_year(brand, model, history, group)
        if by_year.empty:
            continue
        cars = group.merge(by_year, on="year", how="inner")
        if len(cars) < min_used or cars["age"].nunique() < 2:
            continue
        slope, intercept = np.polyfit(cars["age"], np.log(cars["price"] / cars["new_price"]), 1)
        # A flat curve is real (used prices tracking rising 0 km prices, as with the Onix);
        # only a clear rise with age (> 2% a year) is treated as noise.
        if slope > 0.02:
            continue
        # Only read the curve at ages the data actually covers (±1 year): extrapolating a
        # 2019–2021 sample to a 1-year-old car produced nonsense like "keeps 168%".
        low_age, high_age = cars["age"].min() - 1, cars["age"].max() + 1
        kept = {f"kept_{t}y_pct": round(float(np.exp(intercept + slope * t)) * 100, 1)
                if low_age <= t <= high_age else np.nan for t in (1, 3, 5)}
        if any(v > 105 for v in kept.values() if not np.isnan(v)):
            continue  # a used car worth more than new means bad matching, not appreciation
        # The used car's trim is unknown: also read it against the cheapest version.
        base_ratio = float((cars["new_price"] / cars["base_price"]).median())
        kept_3y = kept["kept_3y_pct"]
        rows.append({
            "brand": brand, "model": model, "used_listings": len(cars),
            "years_covered": f"{int(cars['year'].min())}–{int(cars['year'].max())}",
            "median_used_age": cars["age"].median(), **kept,
            "kept_3y_vs_base_pct": np.nan if np.isnan(kept_3y) else round(min(kept_3y * base_ratio, 100.0), 1),
        })
    columns = ["brand", "model", "used_listings", "years_covered", "median_used_age",
               "kept_1y_pct", "kept_3y_pct", "kept_5y_pct", "kept_3y_vs_base_pct"]
    return pd.DataFrame(rows, columns=columns).sort_values("kept_3y_pct", ascending=False).reset_index(drop=True)


def powertrain_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Electric and hybrid stock: share of the market, price, age and leading brands."""
    total = len(df)
    rows = []
    for fuel in ("Eléctrico", "Híbrido"):
        part = df[df["fuel"] == fuel]
        if part.empty:
            continue
        rows.append({
            "fuel": fuel,
            "listings": len(part),
            "share_pct": round(len(part) / total * 100, 2),
            "median_price": part["price"].median(),
            "median_year": part["year"].median(),
            "top_brands": ", ".join(f"{b} ({n})" for b, n in part["brand"].value_counts().head(4).items()),
        })
    return pd.DataFrame(rows).set_index("fuel") if rows else pd.DataFrame()


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
    """Stock size, median price and electrified share per snapshot date."""
    trend = (
        snapshots.groupby("snapshot_date")
        .agg(listings=("id", "count"), median_price=("price", "median"))
        .sort_index()
    )
    if "fuel" in snapshots.columns:
        share = snapshots.assign(ev=snapshots["fuel"].eq("Eléctrico"), hybrid=snapshots["fuel"].eq("Híbrido"))
        by_day = share.groupby("snapshot_date")[["ev", "hybrid"]].mean().mul(100).round(2)
        trend = trend.join(by_day.rename(columns={"ev": "electric_pct", "hybrid": "hybrid_pct"}))
    return trend
