"""Build charts and a Markdown report: python -m vidriera_insights.report [--refresh]."""

import argparse
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # render to files, no window
import matplotlib.pyplot as plt

from . import analysis
from .fetch import load_cards

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "vehicle_cards.csv"
OUT = ROOT / "reports"


def save_bar(series, title: str, xlabel: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    series.plot.barh(ax=ax, color="#2457f5")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def save_curve(curve, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(curve.index, curve["value_kept_pct"], marker="o", color="#2457f5")
    ax.set_title("Valor que conserva un auto según su antigüedad")
    ax.set_xlabel("Antigüedad (años)")
    ax.set_ylabel("% del precio de un auto de 0–1 años")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="download fresh data")
    args = parser.parse_args()

    today = date.today()
    raw = load_cards(CACHE, refresh=args.refresh)
    df = analysis.clean(raw, today.year)
    OUT.mkdir(exist_ok=True)

    brands = analysis.brand_summary(df)
    curve = analysis.depreciation_curve(df)
    km_effect = analysis.mileage_effect(df)
    dealers = analysis.dealer_pricing(df)
    market = analysis.time_on_market(df)

    save_bar(brands["listings"].head(12), "Marcas con más stock", "Autos publicados", OUT / "brands.png")
    save_curve(curve, OUT / "depreciation.png")
    save_bar(dealers["median_vs_fair_pct"], "Automotoras: precio vs. mercado", "% mediano vs. precio justo", OUT / "dealers.png")

    report = f"""# Vidriera Insights — {today:%d/%m/%Y}

Análisis de {len(df):,} autos usados activos (USD) de {df['source_name'].nunique()} automotoras uruguayas,
a partir de los datos públicos de [Vidriera](https://vidriera-uy.vercel.app).

## Marcas con más stock
![](brands.png)

{brands.head(12).round(0).to_markdown()}

## Depreciación
![](depreciation.png)

{curve.to_markdown()}

## Kilometraje
A igual marca, modelo y año, cada **10.000 km extra** cambian el precio en **USD {km_effect:,.0f}**.

## Cómo pone precio cada automotora
Negativo = más barata que autos comparables.
![](dealers.png)

{dealers.to_markdown()}

## ¿Los autos caros tardan más en venderse?
{market.to_markdown()}

> Vidriera registra datos desde el {raw['first_seen_at'].min():%d/%m/%Y}: esta tabla gana sentido
> a medida que se acumulan semanas de historia (días publicados y rebajas de precio).
"""
    (OUT / "REPORT.md").write_text(report, encoding="utf-8")
    print(f"Report written to {OUT / 'REPORT.md'}")


if __name__ == "__main__":
    main()
