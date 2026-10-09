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


def test_model_depreciation_separates_age_from_mileage():
    # Price = 20000 * 0.95^age * 0.97^(km / 10k), with km varying independently of age.
    rows = []
    for age in range(0, 8):
        for km in (10_000 * age, 10_000 * age + 30_000, 10_000 * age + 60_000):
            rows.append({"brand": "Fiat", "model": "Uno", "age": age, "year": 2026 - age, "mileage_km": km,
                         "price": 20000 * 0.95**age * 0.97 ** (km / 10_000)})
    row = analysis.model_depreciation(make_df(rows)).iloc[0]
    assert row["yearly_loss_pct"] == pytest.approx(5.0, abs=0.1)
    assert row["loss_per_10k_km_pct"] == pytest.approx(3.0, abs=0.1)
    # The age-only fit absorbs the extra 10k km per year: 1 - 0.95 * 0.97 = 7.85%.
    assert row["total_yearly_loss_pct"] == pytest.approx(7.85, abs=0.1)


def test_infer_fuel_fills_only_missing_values():
    df = pd.DataFrame({
        "fuel": [None, None, "Nafta", None],
        "title": ["BYD Seagull 2025", "Toyota Corolla Cross Hybrid", "Chevrolet Onix EV look", "Chevrolet Onix"],
        "version": [None, None, None, "1.0 Turbo"],
    })
    assert analysis.infer_fuel(df).tolist()[:3] == ["Eléctrico", "Híbrido", "Nafta"]
    assert pd.isna(analysis.infer_fuel(df).iloc[3])  # "Chevrolet" must not match "hev"


def test_depreciation_from_new_matches_versions_by_prefix():
    new = pd.DataFrame({"brand": ["Chevrolet"] * 3, "name": ["Onix 1.0 LT", "Onix 1.0 Premier", "Onix Plus LTZ"],
                        "price": [20000.0, 24000.0, 26000.0]})
    assert analysis.new_price_for("Chevrolet", "Onix", new) == 24000.0  # median of the three
    assert analysis.new_price_for("Chevrolet", "Tracker", new) is None


def test_depreciation_from_new_uses_the_price_of_each_model_year():
    # The 0 km price rose 5% a year (20,000 in 2022 -> 24,310 in 2026). Each used car keeps
    # 80% of ITS year's new price at age 1 and loses 10% per year after that, so measured
    # against its own year it shows exactly that curve; today's price would overstate the loss.
    history = pd.DataFrame([{"year": y, "brand": "Chevrolet", "name": "Onix 1.0 LT",
                             "price": 20000 * 1.05 ** (y - 2022)} for y in range(2022, 2027)])
    rows = [{"brand": "Chevrolet", "model": "Onix", "age": a, "year": 2026 - a, "version": "LT",
             "price": 20000 * 1.05 ** (2026 - a - 2022) * 0.8 * 0.9 ** (a - 1)} for a in (1, 2, 3, 4) for _ in range(3)]
    table = analysis.depreciation_from_new(make_df(rows), history)
    assert table.loc[0, "kept_1y_pct"] == pytest.approx(80.0, abs=0.1)
    assert table.loc[0, "kept_3y_pct"] == pytest.approx(64.8, abs=0.1)
    assert table.loc[0, "kept_5y_pct"] == pytest.approx(52.5, abs=0.1)  # one year past the data: allowed
    by_year = analysis.new_price_by_year("Chevrolet", "Onix", history)
    assert by_year["year"].tolist() == [2022, 2023, 2024, 2025, 2026]


def test_powertrain_summary_counts_share():
    rows = [{"brand": "Byd", "price": 20000, "year": 2025, "fuel": "Eléctrico"}] * 2
    rows += [{"brand": "Fiat", "price": 10000, "year": 2020, "fuel": "Nafta"}] * 8
    table = analysis.powertrain_summary(make_df(rows))
    assert table.loc["Eléctrico", "share_pct"] == 20.0
    assert "Híbrido" not in table.index


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


def test_new_versions_skip_other_powertrains_and_rare_sub_models():
    new = pd.DataFrame({
        "brand": ["Chevrolet"] * 2 + ["Suzuki"] * 4,
        "name": ["Captiva XL LTZ 1.5 T", "Captiva EV Premier (60 kWh)",
                 "Swift Hybrid 1.2 GLX M/T", "Swift Hybrid 1.2 GLX CVT", "Swift Sport 1.4 M/T", "Swift Sport 1.4 A/T"],
        "price": [34990.0, 31990.0, 22990.0, 24990.0, 30590.0, 33590.0],
    })
    used_captiva = pd.DataFrame({"fuel": ["Nafta"] * 5, "version": ["Premier"] * 5, "title": ["Captiva"] * 5})
    used_swift = pd.DataFrame({"fuel": ["Nafta"] * 5, "version": ["GL 1.2"] * 5, "title": ["Swift"] * 5})
    captiva = analysis.new_versions_for("Chevrolet", "Captiva", new, used_captiva)
    swift = analysis.new_versions_for("Suzuki", "Swift", new, used_swift)
    assert captiva["name"].tolist() == ["Captiva XL LTZ 1.5 T"]  # petrol used cars aren't compared with the EV
    # "Sport" is a different car; the new Swift is only sold as a hybrid, so those versions stay.
    assert swift["name"].tolist() == ["Swift Hybrid 1.2 GLX M/T", "Swift Hybrid 1.2 GLX CVT"]
