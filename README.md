# Vidriera Insights

Market analysis of the Uruguayan used-car market, built in Python on top of the public data from
[Vidriera](https://vidriera-uy.vercel.app) — my aggregator of ~2,300 cars from 27 dealerships.

It answers questions a buyer (or a dealer) actually cares about:

- **Which brands dominate dealer stock**, and at what typical price, year and mileage.
- **How fast cars lose value**: median price by age, as % of a 0–1 year-old car.
- **What mileage really costs**: USD per extra 10,000 km, comparing cars of the *same model and year*
  so age doesn't get mixed into the estimate.
- **Which dealers price above or below the market**, using Vidriera's comparable-based fair price.
- **Whether overpriced cars stay listed longer** (gains meaning as history accumulates).

See the latest output in [`reports/REPORT.md`](reports/REPORT.md).

## Stack

Python 3.11+ · pandas · NumPy · matplotlib · requests · pytest

## Run it

```bash
python -m venv .venv
.venv/Scripts/activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -e ".[dev]"
python -m vidriera_insights.report --refresh   # downloads data, writes reports/
pytest
```

## How it works

| Module | Role |
|---|---|
| `fetch.py` | Pages through the Supabase REST API (`vehicle_cards` view, 1,000 rows per request) and caches a CSV. |
| `analysis.py` | Pure pandas functions — cleaning, group-bys, the within-model mileage regression. No I/O, so they're unit-tested with small fixtures. |
| `report.py` | Renders the charts and the Markdown report. |
