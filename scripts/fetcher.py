"""
Date-aware HTTP fetching for gold price sources.
"""
from datetime import date

import requests

from parsers import HEADERS, normalize_prices, parse_generic
from schemas import PriceEntry


def fetch_html(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def webgia_url(d: date) -> str:
    return f"https://webgia.com/gia-vang/sjc/{d.strftime('%d-%m-%Y')}.html"


def h24_url(d: date) -> str:
    return f"https://www.24h.com.vn/gia-vang-hom-nay-c425.html?ngaythang={d.strftime('%Y-%m-%d')}"


# Sources with known date-parameterized URL patterns.
HISTORICAL_SOURCES = [
    (webgia_url, parse_generic),
    (h24_url, parse_generic),
]


def one_year_ago(today: date) -> date:
    """Return the same calendar date one year prior. Feb 29 falls back to Feb 28."""
    try:
        return today.replace(year=today.year - 1)
    except ValueError:
        return today.replace(year=today.year - 1, day=28)


def to_price_dict(normalized: list[dict]) -> dict[str, PriceEntry]:
    """Convert normalize_prices() list output to {gold_type: PriceEntry} dict."""
    return {
        entry["gold_type"]: {"buy": entry["buy_price"], "sell": entry["sell_price"]}
        for entry in normalized
    }


def _fetch_historical(d: date) -> tuple[dict[str, PriceEntry] | None, str | None]:
    """Try each date-parameterized source in order."""
    for url_fn, parser in HISTORICAL_SOURCES:
        url = url_fn(d)
        print(f"Trying {url} ...")
        try:
            html = fetch_html(url)
            raw = parser(html)
            if raw:
                prices = to_price_dict(normalize_prices(raw))
                if prices:
                    print(f"  -> Got {len(prices)} entries")
                    return prices, url
            print("  -> Parsed OK but no prices found, trying next source")
        except requests.RequestException as e:
            print(f"  -> Request failed: {e}, trying next source")
    return None, None


def fetch_for_date(d: date) -> tuple[dict[str, PriceEntry] | None, str | None]:
    """
    Fetch gold prices for a given date.
    Returns (prices_dict, source_url) on success, or (None, None) on failure.
    Never raises.
    """
    return _fetch_historical(d)
