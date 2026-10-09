"""Price prediction model: learn a car's market price from its specs.

Vidriera's own "fair price" is the median of comparable cars (same model, year ±1,
similar km). This model tries to beat that baseline with gradient boosting, which
can also price cars that have too few exact comparables.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from sklearn.model_selection import KFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

CATEGORICAL = ["brand", "model", "fuel", "transmission", "body_type"]
NUMERIC = ["age", "mileage_km"]
FEATURES = CATEGORICAL + NUMERIC
RARE = "other"
MAX_CATEGORIES = 250  # HistGradientBoosting accepts at most 255 categories per feature


def keep_frequent(values: pd.Series, min_count: int = 3) -> set[str]:
    """Categories seen at least `min_count` times, capped to the most common ones."""
    counts = values.value_counts()
    return set(counts[counts >= min_count].index[:MAX_CATEGORIES])


@dataclass
class Evaluation:
    train_size: int
    test_size: int
    mae_usd: float
    mape_pct: float
    baseline_mae_usd: float | None
    baseline_mape_pct: float | None
    baseline_coverage_pct: float


def mape(actual: pd.Series, predicted: pd.Series) -> float:
    """Mean absolute percentage error, as a rounded percentage."""
    return round(mean_absolute_percentage_error(actual, predicted) * 100, 1)


def build_pipeline(quantile: float | None = None) -> Pipeline:
    """Ordinal-encode categories and feed them natively to gradient boosting.

    With ``quantile`` set, the model predicts that quantile of log(price) instead of
    the mean, which gives the low and high ends of a price range.
    """
    encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1, encoded_missing_value=-1)
    preprocess = ColumnTransformer(
        [("categories", encoder, CATEGORICAL)],
        remainder="passthrough",  # numeric columns go through untouched; NaN is handled by the model
        verbose_feature_names_out=False,
    )
    loss = {"loss": "quantile", "quantile": quantile} if quantile is not None else {}
    model = HistGradientBoostingRegressor(
        **loss,
        categorical_features=list(range(len(CATEGORICAL))),
        learning_rate=0.06,
        max_iter=600,
        l2_regularization=1.0,
        random_state=42,
    )
    return Pipeline([("preprocess", preprocess), ("model", model)])


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    data = df.dropna(subset=["model"]).copy()
    for col in CATEGORICAL:
        data[col] = data[col].astype("string").fillna("unknown")
    return data


def train_and_evaluate(df: pd.DataFrame, seed: int = 42) -> tuple[Pipeline, Evaluation, pd.DataFrame]:
    """Fit on 80% of the cars, report error on the held-out 20%."""
    train, test = train_test_split(prepare(df), test_size=0.2, random_state=seed)
    return fit_split(train, test)


def fit_split(train: pd.DataFrame, test: pd.DataFrame) -> tuple[Pipeline, Evaluation, pd.DataFrame]:
    """Train on one split and score the other.

    The target is log(price): errors become relative, so a USD 2k miss on a
    USD 8k car weighs more than on a USD 40k one.
    """
    # Rare models are learned from the training split only, so no test info leaks in.
    train, test = collapse_rare(train, test)

    pipeline = build_pipeline()
    pipeline.fit(train[FEATURES], np.log(train["price"]))
    test = test.assign(predicted=np.exp(pipeline.predict(test[FEATURES])))

    with_baseline = test.dropna(subset=["fair_price"])
    has_baseline = len(with_baseline) > 0
    evaluation = Evaluation(
        train_size=len(train),
        test_size=len(test),
        mae_usd=round(mean_absolute_error(test["price"], test["predicted"]), 0),
        mape_pct=mape(test["price"], test["predicted"]),
        baseline_mae_usd=round(mean_absolute_error(with_baseline["price"], with_baseline["fair_price"]), 0)
        if has_baseline else None,
        baseline_mape_pct=mape(with_baseline["price"], with_baseline["fair_price"]) if has_baseline else None,
        baseline_coverage_pct=round(len(with_baseline) / len(test) * 100, 1),
    )
    return pipeline, evaluation, test


def model_vs_baseline_on_same_cars(test: pd.DataFrame) -> tuple[float, float]:
    """MAPE of model and baseline restricted to cars both can price (fair comparison)."""
    both = test.dropna(subset=["fair_price"])
    return mape(both["price"], both["predicted"]), mape(both["price"], both["fair_price"])


def best_deals(test: pd.DataFrame, top: int = 10) -> pd.DataFrame:
    """Held-out cars listed furthest below what the model expects.

    Only well-known models with known mileage: for rare models the prediction is
    too uncertain to call anything a bargain.
    """
    known = test[(test["model"] != RARE) & test["mileage_km"].notna()]
    deals = known.assign(discount_pct=((known["predicted"] - known["price"]) / known["predicted"] * 100).round(1))
    cols = ["brand", "model", "year", "mileage_km", "price", "predicted", "discount_pct"]
    return deals.sort_values("discount_pct", ascending=False)[cols].head(top).round({"predicted": 0})


def cross_validate(df: pd.DataFrame, folds: int = 5, seed: int = 42) -> pd.DataFrame:
    """K-fold metrics, so the reported error doesn't hinge on one lucky split."""
    data = prepare(df)
    rows = []
    for train_idx, test_idx in KFold(folds, shuffle=True, random_state=seed).split(data):
        _, evaluation, test = fit_split(data.iloc[train_idx], data.iloc[test_idx])
        model_mape, baseline_mape = model_vs_baseline_on_same_cars(test)
        rows.append({
            "mape_all_pct": evaluation.mape_pct,
            "mae_all_usd": evaluation.mae_usd,
            "mape_with_comparables_pct": model_mape,
            "baseline_mape_pct": baseline_mape,
            "baseline_coverage_pct": evaluation.baseline_coverage_pct,
        })
    return pd.DataFrame(rows)


def permutation_importance_pct(df: pd.DataFrame, seed: int = 42) -> list[float]:
    """Share of R² lost when each feature is shuffled on the test split, in FEATURES order."""
    from sklearn.inspection import permutation_importance

    pipeline, _, test = train_and_evaluate(df, seed)
    result = permutation_importance(
        pipeline, test[FEATURES], np.log(test["price"]), n_repeats=5, random_state=seed
    )
    total = result.importances_mean.clip(min=0).sum()
    return [float(v / total * 100) if total else 0.0 for v in result.importances_mean.clip(min=0)]


def collapse_rare(train: pd.DataFrame, *others: pd.DataFrame) -> tuple[pd.DataFrame, ...]:
    """Map models seen fewer than 3 times in `train` to RARE, in train and the other frames."""
    kept = keep_frequent(train["model"])
    return tuple(frame.assign(model=frame["model"].where(frame["model"].isin(kept), RARE))
                 for frame in (train, *others))


def out_of_fold_ranges(df: pd.DataFrame, folds: int = 5, seed: int = 42, low: float = 0.1,
                       high: float = 0.9) -> pd.DataFrame:
    """Low/high quantile predictions (log scale) for every car, from models that never saw it."""
    data = prepare(df)
    parts = []
    for train_idx, test_idx in KFold(folds, shuffle=True, random_state=seed).split(data):
        train, test = collapse_rare(data.iloc[train_idx], data.iloc[test_idx])
        target = np.log(train["price"])
        lo = build_pipeline(low).fit(train[FEATURES], target).predict(test[FEATURES])
        hi = build_pipeline(high).fit(train[FEATURES], target).predict(test[FEATURES])
        parts.append(pd.DataFrame({"fold": len(parts), "log_price": np.log(test["price"]).to_numpy(),
                                   "lo": np.minimum(lo, hi), "hi": np.maximum(lo, hi)}, index=test.index))
    return pd.concat(parts)


def conformal_margin(ranges: pd.DataFrame, target: float = 0.8) -> float:
    """How much to widen [lo, hi] (in log price) so `target` of cars fall inside.

    Conformalized quantile regression: the score max(lo - y, y - hi) is how far a car
    landed outside its range (negative = inside); its `target` quantile is the margin.
    """
    scores = np.maximum(ranges["lo"] - ranges["log_price"], ranges["log_price"] - ranges["hi"])
    return float(np.quantile(scores, target))


def interval_coverage(df: pd.DataFrame, target: float = 0.8, **kwargs) -> pd.DataFrame:
    """Coverage of the raw quantile range and of the conformally widened one, per fold.

    The margin applied to each fold is estimated on the *other* folds, so the
    calibrated coverage is measured on cars that didn't influence it.
    """
    ranges = out_of_fold_ranges(df, **kwargs)
    rows = []
    for fold, part in ranges.groupby("fold"):
        margin = conformal_margin(ranges[ranges["fold"] != fold], target)
        raw = (part["log_price"] >= part["lo"]) & (part["log_price"] <= part["hi"])
        cal = (part["log_price"] >= part["lo"] - margin) & (part["log_price"] <= part["hi"] + margin)
        width = np.exp(part["hi"] + margin) / np.exp(part["lo"] - margin) - 1
        rows.append({
            "raw_coverage_pct": round(raw.mean() * 100, 1),
            "calibrated_coverage_pct": round(cal.mean() * 100, 1),
            "margin_log": round(margin, 3),
            "median_width_pct": round(float(np.median(width)) * 100, 1),
        })
    return pd.DataFrame(rows)


def fit_price_range(df: pd.DataFrame, low: float = 0.1, high: float = 0.9,
                    target: float = 0.8) -> tuple[dict[str, Pipeline], float]:
    """Median and low/high quantile models on every car, plus the conformal margin."""
    margin = conformal_margin(out_of_fold_ranges(df, low=low, high=high), target)
    (data,) = collapse_rare(prepare(df))
    log_price = np.log(data["price"])
    models = {name: build_pipeline(q).fit(data[FEATURES], log_price)
              for name, q in (("low", low), ("mid", 0.5), ("high", high))}
    return models, margin
