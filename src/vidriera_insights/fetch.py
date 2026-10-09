"""Download the public `vehicle_cards` view from Vidriera's Supabase REST API."""

from pathlib import Path

import pandas as pd
import requests

SUPABASE_URL = "https://qeewxdoextfqvyphmsdm.supabase.co"
# Publishable key: safe to ship, the view is read-only for anonymous users.
PUBLISHABLE_KEY = "sb_publishable_P-P1DBqy9OwTbOFLmuspZA_NzUAxivN"

COLUMNS = [
    "id", "source_id", "source_name", "title", "price", "currency", "status",
    "first_seen_at", "days_listed", "brand", "model", "version", "year",
    "mileage_km", "fuel", "transmission", "body_type", "first_price",
    "price_changes", "fair_price", "fair_sample_size", "price_vs_fair_pct",
]
PAGE_SIZE = 1000


def fetch_cards(session: requests.Session | None = None) -> pd.DataFrame:
    """Fetch every row, paging with the Range header (PostgREST caps pages at 1000)."""
    session = session or requests.Session()
    headers = {"apikey": PUBLISHABLE_KEY}
    rows: list[dict] = []
    start = 0
    while True:
        response = session.get(
            f"{SUPABASE_URL}/rest/v1/vehicle_cards",
            params={"select": ",".join(COLUMNS), "order": "id"},
            headers={**headers, "Range": f"{start}-{start + PAGE_SIZE - 1}"},
            timeout=30,
        )
        response.raise_for_status()
        page = response.json()
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            break
        start += PAGE_SIZE
    return pd.DataFrame(rows, columns=COLUMNS)


def load_cards(cache: Path, refresh: bool = False) -> pd.DataFrame:
    """Return the dataset, downloading it only when there is no cached CSV."""
    if cache.exists() and not refresh:
        return pd.read_csv(cache, parse_dates=["first_seen_at"])
    df = fetch_cards()
    cache.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cache, index=False)
    return pd.read_csv(cache, parse_dates=["first_seen_at"])
