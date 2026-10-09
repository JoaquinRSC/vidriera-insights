# Vidriera Insights

Data analysis and price modelling of the Uruguayan used-car market, in Python, on top of the public data from
[Vidriera](https://vidriera-uy.vercel.app) — my aggregator of **~2,300 cars from 27 dealerships** — plus current
0 km list prices from [Autoblog Uruguay](https://www.autoblog.com.uy/p/precios-0km.html).

![Listed vs. predicted price](reports/predictions.png)

## Key findings (October 2026)

- **A machine-learning price model matches the comparables method (10.6% vs 10.6% error) and prices 100% of
  the stock** — the comparables method can only price ~56% of cars (the rest have too few similar listings).
- **Value kept 3 years after buying new varies a lot**: a Fiat Strada keeps ~84% of today's 0 km price, a
  Chevrolet Onix ~66% and a Peugeot 208 ~60%.
- **Separating age from mileage**, popular models lose between ~1.6% and ~7% per year from age alone, plus
  ~1–2.5% per extra 10,000 km.
- **Within the same model and year, every extra 10,000 km costs ≈ USD 190.**
- **Electric cars are still rare in the used market**: 19 cars (0.8%), almost all 2024–2026 and led by BYD;
  hybrids are 33 (1.4%). Weekly snapshots track how that share grows.
- **Dealers price very differently**: the cheapest list ~7–11% below comparable cars, the priciest ~10–16% above.

Full, regenerated-weekly output: [`reports/REPORT.md`](reports/REPORT.md).

## What's inside

| Analysis | Method |
|---|---|
| Brand and segment summaries | pandas group-bys with a minimum sample size per group; missing fuel inferred from the title ("EV", "Hybrid", "Seagull"…) |
| Overall depreciation curve | median price by age as % of 0–1 year-old cars *in the used stock*; descriptive only, since it mixes models (newer stock skews to SUVs and Chinese brands) |
| **Per-model depreciation** | two log-linear fits per model: `log(price) ~ age` (total yearly loss a buyer sees) and `log(price) ~ age + km` (loss from age alone, and per 10,000 km) |
| **Depreciation from new** | `log(used / 0 km list price) ~ age` on cars up to 6 years old (same generation); 0 km price = median of the model’s comparable versions in Autoblog’s list (same powertrain, no rare sub-models such as "Swift Sport"), read against the median and the cheapest version since the used trim is unknown; free intercept captures the first-owner discount |
| Cost of mileage | within-group regression: prices and km are demeaned per (brand, model, year), so age doesn't leak into the km effect |
| **Price model** | `HistGradientBoostingRegressor` on brand, model, fuel, gearbox, body, age and km; `log(price)` target; rare models collapsed using training data only; 5-fold cross-validation; permutation importance |
| Electric & hybrid market | share, price, age and brands; share tracked over time from snapshots |
| Dealer pricing | median % vs. comparable-based fair price, optional anonymization |
| Market history | dated snapshots saved on every refresh → stock, price and electrified-share trends |

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
| `src/vidriera_insights/fetch.py` | Pages through the Supabase REST API (`vehicle_cards` view, 1,000 rows per request), parses Autoblog's 0 km price list, caches CSVs and stores dated snapshots. |
| `src/vidriera_insights/analysis.py` | Pure pandas/NumPy functions — no I/O, unit-tested with small fixtures. |
| `src/vidriera_insights/model.py` | scikit-learn pipeline, evaluation against the comparables baseline, cross-validation, feature importance. |
| `src/vidriera_insights/report.py` | CLI that renders the charts and the Markdown report. |
| `tests/` | 17 tests, including synthetic markets with a known price rule the model and the regressions must recover. |
| `.github/workflows/` | CI (ruff + pytest) on every push; a weekly job that refreshes data and commits the new report. |

## Limitations

- Listed prices, not transaction prices: what dealers ask, not what buyers pay.
- Per-model depreciation is a cross-section (today's market at different ages), not one car followed over time;
  generations and trims mix, which the 6-year cap only partly controls.
- "From new" uses **today's** 0 km list price, not what the first owner paid, and matches versions by model name.
- Vidriera started collecting on 2026-10-07, so time-on-market and trend sections need a few weeks of history.
- About half the listings don't state gearbox or body type; the model treats them as "unknown".
