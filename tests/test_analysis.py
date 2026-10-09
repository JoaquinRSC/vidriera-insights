import pandas as pd
import pytest

from vidriera_insights import analysis


def make_df(rows):
    base = {
        "status": "active", "currency": "USD", "source_name": "Dealer A",
        "days_listed": 10, "price_changes": 0, "price_vs_fair_pct": 0.0, "model": "Onix",
    }
    return pd.DataFrame([{**base, "id": i, **r} for i, r in enumerate(rows)])


def test_clean_drops_non_usd_inactive_and_absurd_values():
    df = make_df([
        {"brand": "chevrolet", "price": 15000, "year": 2020, "mileage_km": 50000},
        {"brand": "Fiat", "price": 15000, "year": 2020, "mileage_km": 1, "currency": "UYU"},
        {"brand": "Fiat", "price": 15000, "year": 2020, "mileage_km": 1, "status": "removed"},
        {"brand": "Fiat", "price": 50, "year": 2020, "mileage_km": 1},
        {"brand": "Fiat", "price": 9000, "year": 2015, "mileage_km": 5_000_000},
    ])
    out = analysis.clean(df, today_year=2026)
    assert list(out["brand"]) == ["Chevrolet", "Fiat"]
    assert out["age"].tolist() == [6, 11]
    assert pd.isna(out.iloc[1]["mileage_km"])


def test_mileage_effect_isolates_km_within_same_model_year():
    # Same model/year: every 10,000 km costs exactly USD 500.
    rows = [{"brand": "Fiat", "model": "Uno", "year": 2018, "mileage_km": km, "price": 10000 - km / 20}
            for km in (20000, 40000, 60000, 80000)]
    # A different year with a different price level must not distort the slope.
    rows += [{"brand": "Fiat", "model": "Uno", "year": 2012, "mileage_km": km, "price": 5000 - km / 20}
             for km in (100000, 120000, 140000)]
    assert analysis.mileage_effect(make_df(rows)) == pytest.approx(-500)


def test_dealer_pricing_requires_minimum_sample():
    rows = [{"brand": "Fiat", "price": 1, "year": 2020, "source_name": "Big", "price_vs_fair_pct": 8.0}] * 12
    rows += [{"brand": "Fiat", "price": 1, "year": 2020, "source_name": "Tiny", "price_vs_fair_pct": -20.0}] * 3
    table = analysis.dealer_pricing(make_df(rows))
    assert list(table.index) == ["Big"]
    assert table.loc["Big", "share_above_fair"] == 100.0


def test_model_depreciation_recovers_constant_yearly_loss():
    # Price drops exactly 10% per year -> yearly_loss_pct must be 10.
    rows = [{"brand": "Fiat", "model": "Uno", "age": age, "year": 2026 - age, "price": 20000 * 0.9**age}
            for age in range(0, 8) for _ in range(3)]
    table = analysis.model_depreciation(make_df(rows))
    assert table.loc[0, "yearly_loss_pct"] == pytest.approx(10.0)


def test_segment_summary_ignores_missing_and_small_groups():
    rows = [{"brand": "Fiat", "price": 10000, "age": 5, "fuel": "Nafta"}] * 12
    rows += [{"brand": "Fiat", "price": 30000, "age": 2, "fuel": "Híbrido"}] * 2
    rows += [{"brand": "Fiat", "price": 1, "age": 1, "fuel": None}] * 20
    table = analysis.segment_summary(make_df(rows), "fuel")
    assert list(table.index) == ["Nafta"]


def test_dealer_pricing_anonymizes_names():
    rows = [{"brand": "Fiat", "price": 1, "year": 2020, "source_name": "Real Name", "price_vs_fair_pct": 1.0}] * 12
    table = analysis.dealer_pricing(make_df(rows), anonymize=True)
    assert list(table.index) == ["Automotora A"]


def test_market_trend_orders_snapshots():
    snaps = pd.DataFrame({
        "id": [1, 2, 3], "price": [10, 20, 30],
        "snapshot_date": pd.to_datetime(["2026-10-16", "2026-10-09", "2026-10-16"]),
    })
    trend = analysis.market_trend(snaps)
    assert list(trend["listings"]) == [1, 2]
