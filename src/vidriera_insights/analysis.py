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


def mileage_effect(df: pd.DataFrame) -> float:
    """USD lost per extra 10,000 km for cars of the same model and year.

    Prices are demeaned within each (brand, model, year) group, so the slope only
    reflects mileage, not the fact that older cars have both more km and lower prices.
    """
    data = df.dropna(subset=["mileage_km", "model"]).copy()
    groups = data.groupby(["brand", "model", "year"])
    data = data[groups["id"].transform("count") >= 3]
    data["price_dev"] = data["price"] - data.groupby(["brand", "model", "year"])["price"].transform("mean")
    data["km_dev"] = data["mileage_km"] - data.groupby(["brand", "model", "year"])["mileage_km"].transform("mean")
    slope, _ = np.polyfit(data["km_dev"], data["price_dev"], 1)
    return round(slope * 10_000, 2)


def dealer_pricing(df: pd.DataFrame) -> pd.DataFrame:
    """How each dealer prices against the market (median % vs. fair price)."""
    priced = df.dropna(subset=["price_vs_fair_pct"])
    table = priced.groupby("source_name").agg(
        listings=("id", "count"),
        median_vs_fair_pct=("price_vs_fair_pct", "median"),
        share_above_fair=("price_vs_fair_pct", lambda s: round((s > 5).mean() * 100, 1)),
    )
    return table[table["listings"] >= MIN_SAMPLE].sort_values("median_vs_fair_pct")


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
