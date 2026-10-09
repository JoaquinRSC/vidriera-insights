import numpy as np
import pandas as pd
import pytest

from vidriera_insights import model


def synthetic_market(n: int = 400, seed: int = 0) -> pd.DataFrame:
    """Cars whose price follows a known rule, so the model has something to learn."""
    rng = np.random.default_rng(seed)
    brands = rng.choice(["Fiat", "Toyota", "Chevrolet"], n)
    base = pd.Series(brands).map({"Fiat": 12000, "Toyota": 25000, "Chevrolet": 15000}).to_numpy()
    age = rng.integers(0, 15, n)
    km = age * 12000 + rng.integers(0, 20000, n)
    price = base * 0.92**age - km * 0.02 + rng.normal(0, 300, n)
    return pd.DataFrame({
        "id": range(n), "brand": brands, "model": pd.Series(brands) + " base",
        "fuel": "Nafta", "transmission": "Manual", "body_type": None,
        "age": age, "year": 2026 - age, "mileage_km": km, "price": price.clip(min=1500),
        "fair_price": np.where(rng.random(n) < 0.5, price, np.nan),
    })


def test_keep_frequent_caps_and_filters():
    values = pd.Series(["a"] * 5 + ["b"] * 3 + ["c"] * 1)
    assert model.keep_frequent(values) == {"a", "b"}


def test_model_learns_a_clear_price_rule():
    _, evaluation, test = model.train_and_evaluate(synthetic_market())
    assert evaluation.mape_pct < 10
    assert evaluation.test_size == len(test) == 80
    assert 30 < evaluation.baseline_coverage_pct < 70


def test_cross_validate_returns_one_row_per_fold():
    cv = model.cross_validate(synthetic_market(), folds=3)
    assert len(cv) == 3
    assert (cv["mape_all_pct"] < 10).all()


def test_unseen_categories_do_not_crash_prediction():
    pipeline, _, _ = model.train_and_evaluate(synthetic_market())
    new_car = pd.DataFrame([{
        "brand": "Tesla", "model": "other", "fuel": "Eléctrico", "transmission": "Automática",
        "body_type": "unknown", "age": 1, "mileage_km": 10000,
    }])
    assert np.isfinite(pipeline.predict(new_car[model.FEATURES])).all()


def test_best_deals_skips_rare_models():
    test = pd.DataFrame({
        "brand": ["A", "B"], "model": [model.RARE, "Known"], "year": [2020, 2020],
        "mileage_km": [1000, 1000], "price": [5000, 9000], "predicted": [20000, 10000],
    })
    deals = model.best_deals(test)
    assert list(deals["model"]) == ["Known"]
    assert deals.iloc[0]["discount_pct"] == pytest.approx(10.0)
