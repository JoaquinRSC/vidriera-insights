# Vidriera Insights

Data analysis and price modelling of the Uruguayan used-car market, in Python, on top of the public data from
[Vidriera](https://vidriera-uy.vercel.app) — my aggregator of **~2,300 cars from 27 dealerships**.

![Listed vs. predicted price](reports/predictions.png)

## Key findings (October 2026)

- **A machine-learning price model matches the comparables method (10.6% vs 10.6% error) and prices 100% of
  the stock** — the comparables method can only price ~56% of cars (the rest have too few similar listings).
- **Age explains the most** (~43% of the model's explanatory power), followed by brand and model; mileage adds ~5%.
- **Within the same model and year, every extra 10,000 km costs ≈ USD 190.**
- **Value retention varies 3× across popular models**: from ~2.4%/year (VW Gol) to ~7%/year (Nissan Versa).
- **Dealers price very differently**: the cheapest list ~7–11% below comparable cars, the priciest ~10–16% above.

Full, regenerated-weekly output: [`reports/REPORT.md`](reports/REPORT.md).

## What's inside

| Analysis | Method |
|---|---|
| Brand and segment summaries | pandas group-bys with a minimum sample size per group |
| Depreciation curve | median price by age, normalized to a 0–1 year-old car |
| Per-model depreciation | log-linear fit `log(price) = a + b·age` → constant % loss per year |
| Cost of mileage | within-group regression: prices and km are demeaned per (brand, model, year), so age doesn't leak into the km effect |
| **Price model** | `HistGradientBoostingRegressor` on brand, model, fuel, gearbox, body, age and km; `log(price)` target; rare models collapsed using training data only; 5-fold cross-validation; permutation importance |
| Dealer pricing | median % vs. comparable-based fair price, optional anonymization |
| Market history | dated snapshots saved on every refresh → stock and price trends over time |

## Stack

Python 3.11+ · pandas · NumPy · scikit-learn · matplotlib · requests · pytest · ruff · GitHub Actions

## Run it

```bash
python -m venv .venv
.venv/Scripts/activate            # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -e ".[dev]"
python -m vidriera_insights.report --refresh            # download data, save snapshot, write reports/
python -m vidriera_insights.report --anonymize-dealers  # same report without dealer names
pytest && ruff check src tests
```

## Project layout

| Path | Role |
|---|---|
| `src/vidriera_insights/fetch.py` | Pages through the Supabase REST API (`vehicle_cards` view, 1,000 rows per request), caches a CSV and stores dated snapshots. |
| `src/vidriera_insights/analysis.py` | Pure pandas/NumPy functions — no I/O, unit-tested with small fixtures. |
| `src/vidriera_insights/model.py` | scikit-learn pipeline, evaluation against the comparables baseline, cross-validation, feature importance. |
| `src/vidriera_insights/report.py` | CLI that renders the charts and the Markdown report. |
| `tests/` | 12 tests, including synthetic markets with a known price rule the model must recover. |
| `.github/workflows/` | CI (ruff + pytest) on every push; a weekly job that refreshes data and commits the new report. |

## Limitations

- Listed prices, not transaction prices: what dealers ask, not what buyers pay.
- Vidriera started collecting on 2026-10-07, so time-on-market and trend sections need a few weeks of history.
- About half the listings don't state gearbox or body type; the model treats them as "unknown".
