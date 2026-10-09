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


# --- Historical 0 km prices (Autoblog's list as archived by the Wayback Machine) ---

WAYBACK_CDX = "https://web.archive.org/cdx/search/cdx"
WAYBACK_RAW = "https://web.archive.org/web/{timestamp}id_/https://www.autoblog.com.uy/p/precios-0km.html"
HISTORY_COLUMNS = ["year", "snapshot", "brand", "name", "price"]


def yearly_snapshots(session: requests.Session) -> dict[int, str]:
    """The earliest archived copy of each year (prices for that model year are set early on)."""
    response = session.get(WAYBACK_CDX, params={
        "url": "autoblog.com.uy/p/precios-0km.html", "fl": "timestamp,statuscode", "collapse": "timestamp:6",
    }, timeout=60)
    response.raise_for_status()
    first: dict[int, str] = {}
    for line in response.text.splitlines():
        timestamp, status = line.split()
        if status == "200":
            first.setdefault(int(timestamp[:4]), timestamp)
    return first


def brand_key(text: str) -> str:
    """Lowercase, accent-free, letters and digits only: "Citroën" -> "citroen"."""
    text = text.lower().translate(str.maketrans("áéíóúüëñ", "aeiouuen"))
    return re.sub(r"[^a-z0-9]", "", text)


# Importer websites that don't spell the brand out.
DOMAIN_ALIASES = {"vw": "Volkswagen", "mercedesbenz": "Mercedes-Benz", "gwm": "Gwm"}


def brand_from_header(page: str, position: int, keys: list[tuple[str, str]]) -> str | None:
    """Brand of the price block whose "Importador" line starts at `position`.

    The importer's website right below ("www.citroen.com.uy") is the reliable signal.
    Failing that, the logo's file name just above ("Chevrolet-logo.png") — only the
    file name, since Blogger image URLs are long random strings where short brand
    names like "MG" show up by chance.
    """
    after = page[position: position + 700]
    domain = re.search(r"www\.([a-z0-9-]+)\.", after, re.I)
    if domain:
        domain_key = brand_key(domain[1])
        for alias, brand in DOMAIN_ALIASES.items():
            if domain_key.startswith(alias):
                return brand
        found = next((brand for key, brand in keys if key in domain_key), None)
        if found:
            return found
    logos = re.findall(r'(?:src|href)="[^"]*/([^/"]+)\.(?:png|jpe?g|gif|webp)"',
                       page[max(0, position - 1500): position], re.I)
    if logos:
        logo_key = brand_key(logos[-1])
        return next((brand for key, brand in keys if len(key) >= 3 and key in logo_key), None)
    return None


def parse_archived_prices(page: str, brands: list[str]) -> pd.DataFrame:
    """Brand, name and price from an archived copy, in either of the page's layouts.

    Since 2026 the list is one <section data-brand> per brand. Before that it was a
    blog post: a brand logo, "Importador: ...", "Web: www.<brand>.com.uy" and a list
    of "<b>Model</b> version - price" items. The brand of those items is read from
    the header that precedes them (logo file name, importer and website).
    """
    current = parse_new_car_prices(page)
    if not current.empty:
        return current[["brand", "name", "price"]]

    keys = sorted(((brand_key(b), b) for b in brands if len(brand_key(b)) >= 2), key=lambda kb: -len(kb[0]))
    headers = []
    for match in re.finditer(r"Importador", page):
        found = brand_from_header(page, match.start(), keys)
        if found:
            headers.append((match.start(), found))
    rows = []
    # The bold model name and its version must sit inside one link: without the negative
    # lookahead a "<b>Importador:</b>" header would swallow the first model of each brand.
    item_pattern = r"<b>([^<]*)</b>((?:(?!</a>|<b>).)*)</a>\s*(?:<span[^>]*>)?(?:&nbsp;|\s)*-\s*([\d.]+)"
    for item in re.finditer(item_pattern, page, re.S):
        brand = next((b for pos, b in reversed(headers) if pos < item.start()), None)
        if brand is None:
            continue
        name = html.unescape(re.sub(r"<[^>]+>", " ", item[1] + " " + item[2])).replace("\xa0", " ")
        rows.append({"brand": brand, "name": re.sub(r"\s+", " ", name).strip(),
                     "price": float(item[3].replace(".", ""))})
    return pd.DataFrame(rows, columns=["brand", "name", "price"])


def load_new_price_history(cache: Path, brands: list[str], refresh: bool = False,
                           session: requests.Session | None = None) -> pd.DataFrame:
    """0 km prices per year since the earliest archive, downloading only missing years."""
    history = pd.read_csv(cache) if cache.exists() else pd.DataFrame(columns=HISTORY_COLUMNS)
    if not refresh and not history.empty:
        return history
    session = session or requests.Session()
    known = set(history["year"].astype(int)) if not history.empty else set()
    frames = [history]
    for year, timestamp in sorted(yearly_snapshots(session).items()):
        if year in known:
            continue
        response = session.get(WAYBACK_RAW.format(timestamp=timestamp), timeout=120)
        response.raise_for_status()
        prices = parse_archived_prices(response.text, brands)
        frames.append(prices.assign(year=year, snapshot=timestamp)[HISTORY_COLUMNS])
    history = pd.concat([f for f in frames if not f.empty], ignore_index=True)
    cache.parent.mkdir(parents=True, exist_ok=True)
    history.to_csv(cache, index=False)
    return history
