"""Download the public `vehicle_cards` view from Vidriera's Supabase REST API."""

import html
import re
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
    "price_changes", "fair_price", "fair_sample_size", "price_vs_fair_pct", "url",
]
SNAPSHOT_COLUMNS = [
    "id", "source_id", "title", "version", "price", "currency", "status", "brand", "model", "year",
    "mileage_km", "fuel",
]
PAGE_SIZE = 1000

# Autoblog Uruguay keeps a hand-maintained list of current 0 km list prices for
# every brand sold in the country (USD, VAT included).
AUTOBLOG_PRICES = "https://www.autoblog.com.uy/p/precios-0km.html"
NEW_CAR_COLUMNS = ["brand", "name", "price", "list_updated", "source"]


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


def parse_new_car_prices(page: str) -> pd.DataFrame:
    """Brand, model/version name and USD price for every entry of Autoblog's list."""
    # The date is split across tags ("<b>12</b><strong>/10/2026</strong>"), so match on plain text.
    text = re.sub(r"<[^>]+>", "", page)
    updated = re.search(r"actualizaci[oó]n:\s*(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})", text)
    list_updated = f"{updated[3]}-{int(updated[2]):02d}-{int(updated[1]):02d}" if updated else None
    rows = []
    for brand, body in re.findall(r'<section class="ab-price-brand" data-brand="([^"]+)"(.*?)</section>', page, re.S):
        for name, price in re.findall(
            r'class="ab-price-model">(.*?)</span>\s*<strong class="ab-price-value">U\$S\s*([\d.]+)', body, re.S
        ):
            rows.append({
                "brand": html.unescape(brand).strip().title(),
                "name": re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", name))).strip(),
                "price": float(price.replace(".", "")),
                "list_updated": list_updated,
                "source": "Autoblog Uruguay",
            })
    return pd.DataFrame(rows, columns=NEW_CAR_COLUMNS)


def fetch_new_cars(session: requests.Session | None = None) -> pd.DataFrame:
    """Current 0 km list prices scraped from Autoblog Uruguay."""
    session = session or requests.Session()
    response = session.get(AUTOBLOG_PRICES, timeout=30, headers={"User-Agent": "Mozilla/5.0 (vidriera-insights)"})
    response.raise_for_status()
    return parse_new_car_prices(response.text)


def load_new_cars(cache: Path, refresh: bool = False) -> pd.DataFrame:
    if refresh or not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        fetch_new_cars().to_csv(cache, index=False)
    return pd.read_csv(cache)
