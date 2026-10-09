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
from .fetch import load_cards, load_new_cars, load_new_price_history, load_snapshots, save_snapshot

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "vehicle_cards.csv"
NEW_CARS = ROOT / "data" / "new_cars.csv"
PRICE_HISTORY = ROOT / "data" / "new_price_history.csv"
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
    new_cars = load_new_cars(NEW_CARS, refresh=args.refresh)
    price_history = load_new_price_history(PRICE_HISTORY, sorted(new_cars["brand"].unique()), refresh=args.refresh)
    OUT.mkdir(exist_ok=True)

    brands = analysis.brand_summary(df)
    curve = analysis.depreciation_curve(df)
    by_model = analysis.model_depreciation(df)
    fuel = analysis.segment_summary(df, "fuel")
    gearbox = analysis.segment_summary(df, "transmission")
    km_effect = analysis.mileage_effect(df)
    dealers = analysis.dealer_pricing(df, anonymize=args.anonymize_dealers)
    market = analysis.time_on_market(df)
    from_new = analysis.depreciation_from_new(df, price_history)
    onix_prices = analysis.new_price_by_year("Chevrolet", "Onix", price_history,
                                             df[(df["brand"] == "Chevrolet") & (df["model"] == "Onix")])
    history_years = f"{int(price_history['year'].min())}–{int(price_history['year'].max())}"
    electrified = analysis.powertrain_summary(df)
    electric_cars = df[df["fuel"] == "Eléctrico"].sort_values("price")[
        ["brand", "model", "year", "mileage_km", "price", "source_name"]]
    snapshots = load_snapshots(SNAPSHOTS)
    trend = (analysis.market_trend(analysis.clean(snapshots, today.year)) if not snapshots.empty
             else pd.DataFrame())

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
    if not from_new.empty:
        kept = from_new.dropna(subset=["kept_3y_pct"])
        kept = kept.set_index(kept["brand"] + " " + kept["model"])["kept_3y_pct"]
        bar_chart(kept, "Valor que conserva a los 3 años vs. su precio 0 km", "% del precio 0 km de su año",
                  OUT / "from_new.png")

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

### Curva general
Mediana del precio publicado según la antigüedad, como % de la mediana de los autos de **0–1 año que hoy
están en el stock usado** (no del precio de lista 0 km). Mezcla modelos distintos: los autos nuevos del
stock son más SUVs y marcas chinas que los viejos, así que la curva **exagera** la caída. Para comparar
autos de verdad, ver las tablas por modelo.

![](depreciation.png)

{md(curve)}

### Por modelo, separando edad y kilometraje
Dos regresiones log-lineales por modelo (autos de hasta 12 años, modelos con ≥20 publicaciones):

- `total_yearly_loss_pct`: `log(precio) ~ antigüedad`. La pérdida anual que ve un comprador, que mezcla
  envejecer y sumar kilómetros.
- `yearly_loss_pct`: `log(precio) ~ antigüedad + km`. La pérdida **solo por edad**, a igual kilometraje.
- `loss_per_10k_km_pct`: en la misma regresión, la pérdida por cada **10.000 km** extra a igual edad.

Un valor bajo significa que el modelo **retiene mejor su valor**. Muestras chicas dan coeficientes ruidosos
(un valor negativo en km indica justamente eso).

![](models.png)

{md(by_model, index=False)}

### Desde 0 km
Valor que conserva un usado frente a **lo que costaba 0 km el mismo modelo en su año**. Un Onix 2021 se
compara con el precio del Onix 0 km en 2021, no con el de hoy: los precios nuevos cambian bastante con los años y
usar el de hoy distorsiona la depreciación.

Los precios 0 km de cada año salen de la
[lista de Autoblog Uruguay](https://www.autoblog.com.uy/p/precios-0km.html) tal como la guardó el
[Internet Archive](https://web.archive.org/) a comienzos de cada año ({history_years}, {len(price_history):,}
precios). Por ejemplo, la mediana de las versiones comparables del Onix:

{md(onix_prices, index=False)}

Solo cuentan versiones **comparables** (misma motorización que los usados y sin sub-modelos que casi no aparecen
entre ellos, como el Swift Sport). Se ajusta `log(precio usado / precio 0 km de su año) ~ antigüedad` por modelo y
se lee a 1, 3 y 5 años, **solo dentro de las edades que cubren los datos** (un hueco aparece vacío). Como no se sabe
la versión de cada usado, `kept_3y_pct` compara contra la versión mediana y `kept_3y_vs_base_pct` contra la más
barata: el valor real está entre las dos.

Una curva **plana** (igual % a 1, 3 y 5 años) no es un error: significa que los usados de ese modelo acompañaron
la suba de su precio 0 km, así que uno de 2019 vale, respecto de lo que costó, lo mismo que uno de 2024.

Límites: son precios de lista (sin las bonificaciones de las concesionarias, lo que exagera un poco la pérdida) y
precios publicados de usados (no de venta).

![](from_new.png)

{md(from_new, index=False) if not from_new.empty else "_Todavía no hay modelos con suficientes usados y precio 0 km._"}


## 3. Kilometraje
A igual marca, modelo y año, cada **10.000 km extra** cambian el precio en **USD {km_effect:,.0f}**.

## 4. Combustible y caja
El combustible se completa desde el título cuando el aviso no lo indica (por ejemplo "EV", "Híbrido",
"Seagull"), porque cerca de un cuarto de los avisos no lo cargan.

{md(fuel)}

{md(gearbox)}

### Eléctricos e híbridos
{md(electrified) if not electrified.empty else "_Sin datos._"}

Los eléctricos usados son casi todos de **2024–2026**: el mercado de eléctricos de segunda mano en Uruguay
recién empieza. Con tan pocos autos no tiene sentido estimar su depreciación todavía; la sección 8 sigue
cómo crece su participación semana a semana.

{md(electric_cars, index=False)}

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
Stock, precio mediano y % de eléctricos e híbridos en cada foto semanal.

{trend_section}
"""
    (OUT / "REPORT.md").write_text(report, encoding="utf-8")
    print(f"Report written to {OUT / 'REPORT.md'} (test MAPE {evaluation.mape_pct}%)")


if __name__ == "__main__":
    main()
