"""Download the public `vehicle_cards` view from Vidriera's Supabase REST API."""

from datetime import date
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
SNAPSHOT_COLUMNS = ["id", "source_id", "price", "currency", "status", "brand", "model", "year", "mileage_km"]
PAGE_SIZE = 1000


def fetch_cards(session: requests.Session | None = None) -> pd.DataFrame:
    """Fetch every row, paging with the Range header (PostgREST caps pages at 1000)."""
    session = session or requests.Session()
    rows: list[dict] = []
    start = 0
    while True:
        response = session.get(
            f"{SUPABASE_URL}/rest/v1/vehicle_cards",
            params={"select": ",".join(COLUMNS), "order": "id"},
            headers={"apikey": PUBLISHABLE_KEY, "Range": f"{start}-{start + PAGE_SIZE - 1}"},
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
    if refresh or not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        fetch_cards().to_csv(cache, index=False)
    return pd.read_csv(cache, parse_dates=["first_seen_at"])


def save_snapshot(df: pd.DataFrame, folder: Path, day: date) -> Path:
    """Store a slim daily copy so market trends can be computed over time."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{day:%Y-%m-%d}.csv.gz"
    df[SNAPSHOT_COLUMNS].to_csv(path, index=False)
    return path


def load_snapshots(folder: Path) -> pd.DataFrame:
    """Concatenate every saved snapshot, tagged with its date."""
    frames = [
        pd.read_csv(path).assign(snapshot_date=pd.Timestamp(path.name.removesuffix(".csv.gz")))
        for path in sorted(folder.glob("*.csv.gz"))
    ]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
