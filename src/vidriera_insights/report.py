"""Build charts and a Markdown report.

    python -m vidriera_insights.report [--refresh] [--anonymize-dealers]
"""

import argparse
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # render to files, no window
import matplotlib.pyplot as plt
import pandas as pd

from . import analysis, model
from .fetch import load_cards, load_snapshots, save_snapshot

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "vehicle_cards.csv"
SNAPSHOTS = ROOT / "data" / "snapshots"
OUT = ROOT / "reports"
ACCENT = "#2457f5"


def save_figure(fig, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def bar_chart(series: pd.Series, title: str, xlabel: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, max(3, len(series) * 0.32)))
    colors = [ACCENT if v >= 0 else "#16a34a" for v in series] if series.min() < 0 else ACCENT
    series.plot.barh(ax=ax, color=colors)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("")
    ax.invert_yaxis()
    save_figure(fig, path)


def depreciation_chart(curve: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(curve.index, curve["value_kept_pct"], marker="o", color=ACCENT)
    ax.set_title("Valor que conserva un auto según su antigüedad")
    ax.set_xlabel("Antigüedad (años)")
    ax.set_ylabel("% del precio de un auto de 0–1 años")
    ax.grid(alpha=0.3)
    save_figure(fig, path)


def prediction_chart(test: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(test["price"], test["predicted"], s=10, alpha=0.5, color=ACCENT)
    top = max(test["price"].quantile(0.99), test["predicted"].quantile(0.99))
    ax.plot([0, top], [0, top], color="#999", linestyle="--", linewidth=1)
    ax.set_xlim(0, top)
    ax.set_ylim(0, top)
    ax.set_title("Precio publicado vs. precio predicho (test)")
    ax.set_xlabel("Precio publicado (USD)")
    ax.set_ylabel("Precio predicho (USD)")
    ax.grid(alpha=0.3)
    save_figure(fig, path)


def md(df: pd.DataFrame, **kwargs) -> str:
    return df.to_markdown(**kwargs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="download fresh data and save a snapshot")
    parser.add_argument("--anonymize-dealers", action="store_true", help="hide dealer names in the report")
    args = parser.parse_args()

    today = date.today()
    raw = load_cards(CACHE, refresh=args.refresh)
    if args.refresh:
        save_snapshot(raw, SNAPSHOTS, today)
    df = analysis.clean(raw, today.year)
    OUT.mkdir(exist_ok=True)

    brands = analysis.brand_summary(df)
    curve = analysis.depreciation_curve(df)
    by_model = analysis.model_depreciation(df)
    fuel = analysis.segment_summary(df, "fuel")
    gearbox = analysis.segment_summary(df, "transmission")
    km_effect = analysis.mileage_effect(df)
    dealers = analysis.dealer_pricing(df, anonymize=args.anonymize_dealers)
    market = analysis.time_on_market(df)
    snapshots = load_snapshots(SNAPSHOTS)
    trend = analysis.market_trend(snapshots) if not snapshots.empty else pd.DataFrame()

    cv = model.cross_validate(df)
    _, evaluation, test = model.train_and_evaluate(df)
    no_comparables = test[test["fair_price"].isna()]
    mape_no_comparables = model.mape(no_comparables["price"], no_comparables["predicted"])
    deals = model.best_deals(test)
    importances = (
        pd.Series(dict(zip(model.FEATURES, model.permutation_importance_pct(df), strict=True)))
        .sort_values(ascending=False)
    )

    bar_chart(brands["listings"].head(12), "Marcas con más stock", "Autos publicados", OUT / "brands.png")
    depreciation_chart(curve, OUT / "depreciation.png")
    labels = by_model["brand"] + " " + by_model["model"]
    yearly_loss = by_model.set_index(labels)["yearly_loss_pct"]
    bar_chart(yearly_loss, "Pérdida de valor por año, por modelo", "% por año", OUT / "models.png")
    bar_chart(dealers["median_vs_fair_pct"], "Automotoras: precio vs. mercado", "% mediano vs. precio justo",
              OUT / "dealers.png")
    prediction_chart(test, OUT / "predictions.png")

    cv_mean = cv.mean()
    trend_section = (
        md(trend.round(0))
        if len(trend) > 1
        else "_Se necesita más de una corrida con `--refresh` para ver la evolución._"
    )
    report = f"""# Vidriera Insights — {today:%d/%m/%Y}

Análisis de **{len(df):,} autos usados activos** (USD) de **{df['source_name'].nunique()} automotoras** uruguayas,
a partir de los datos públicos de [Vidriera](https://vidriera-uy.vercel.app).

## 1. Marcas con más stock
![](brands.png)

{md(brands.head(12).round(0))}

## 2. Depreciación
![](depreciation.png)

{md(curve)}

### Por modelo
Pendiente de `log(precio) ~ antigüedad` por modelo (autos de hasta 12 años, modelos con ≥20 publicaciones).
Un valor bajo significa que el modelo **retiene mejor su valor**.

![](models.png)

{md(by_model, index=False)}

## 3. Kilometraje
A igual marca, modelo y año, cada **10.000 km extra** cambian el precio en **USD {km_effect:,.0f}**.

## 4. Combustible y caja
{md(fuel)}

{md(gearbox)}

## 5. Modelo de precio (machine learning)
Gradient boosting (`HistGradientBoostingRegressor`) sobre marca, modelo, combustible, caja, carrocería,
antigüedad y kilometraje, con objetivo `log(precio)`. Validación cruzada de 5 particiones:

| Métrica | Valor |
|---|---|
| Error medio (todos los autos) | **{cv_mean['mape_all_pct']:.1f}%** (USD {cv_mean['mae_all_usd']:,.0f}) |
| Error en autos con comparables — modelo | **{cv_mean['mape_with_comparables_pct']:.1f}%** |
| Error en autos con comparables — precio justo de Vidriera | {cv_mean['baseline_mape_pct']:.1f}% |
| Autos que el método de comparables puede tasar | {cv_mean['baseline_coverage_pct']:.0f}% |
| Error del modelo en autos **sin** comparables | {mape_no_comparables:.1f}% |

El modelo **iguala** al método de comparables donde éste funciona y además **tasa el 100% del stock**,
incluidos los modelos raros que no tienen suficientes autos parecidos.

![](predictions.png)

**Qué pesa más en el precio** (caída del R² al desordenar cada variable):

{md(importances.round(1).to_frame('importancia_pct'))}

**Candidatos a revisar**: autos del set de test publicados más por debajo de lo que espera el modelo
(una señal para mirar de cerca, no una garantía: el aviso puede tener detalles que los datos no capturan).

{md(deals, index=False)}

## 6. Cómo pone precio cada automotora
Negativo = más barata que autos comparables.
![](dealers.png)

{md(dealers)}

## 7. ¿Los autos caros tardan más en venderse?
{md(market)}

> Vidriera registra datos desde el {raw['first_seen_at'].min():%d/%m/%Y}: esta tabla gana sentido
> a medida que se acumulan semanas de historia (días publicados y rebajas de precio).

## 8. Evolución del mercado
{trend_section}
"""
    (OUT / "REPORT.md").write_text(report, encoding="utf-8")
    print(f"Report written to {OUT / 'REPORT.md'} (test MAPE {evaluation.mape_pct}%)")


if __name__ == "__main__":
    main()
