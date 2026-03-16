"""
Date-aware HTTP fetching for gold price sources.
"""
from datetime import date

import requests

from parsers import HEADERS, normalize_prices
from schemas import PriceEntry
from constants import HISTORICAL_SOURCES, SOURCES


def fetch_html(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


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


def scale_prices(normalized: list[dict], multiplier: int) -> list[dict]:
    """Multiply buy/sell prices by multiplier to normalise to VND per lượng."""
    return [
        {**e,
         "buy_price":  e["buy_price"]  * multiplier if e["buy_price"]  is not None else None,
         "sell_price": e["sell_price"] * multiplier if e["sell_price"] is not None else None}
        for e in normalized
    ]


def _fetch_historical(d: date) -> tuple[dict[str, PriceEntry] | None, str | None]:
    """Try each date-parameterized source in order."""
    for url_fn, parser, multiplier in HISTORICAL_SOURCES:
        url = url_fn(d)
        print(f"Trying {url} ...")
        try:
            html = fetch_html(url)
            raw = parser(html)
            if raw:
                normalized = normalize_prices(raw)
                if multiplier != 1:
                    normalized = scale_prices(normalized, multiplier)
                prices = to_price_dict(normalized)
                if prices:
                    print(f"  -> Got {len(prices)} entries")
                    return prices, url
            print("  -> Parsed OK but no prices found, trying next source")
        except requests.RequestException as e:
            print(f"  -> Request failed: {e}, trying next source")
    return None, None


def _fetch_today() -> tuple[dict[str, PriceEntry] | None, str | None]:
    """Try HISTORICAL_SOURCES first (with today's date), then fall back to full SOURCES list."""
    prices, source = _fetch_historical(date.today())
    if prices:
        return prices, source

    for url, parser, multiplier in SOURCES:
        print(f"Trying {url} ...")
        try:
            html = fetch_html(url)
            raw = parser(html)
            if raw:
                normalized = normalize_prices(raw)
                if multiplier != 1:
                    normalized = scale_prices(normalized, multiplier)
                result = to_price_dict(normalized)
                if result:
                    print(f"  -> Got {len(result)} entries")
                    return result, url
            print("  -> Parsed OK but no prices found, trying next source")
        except requests.RequestException as e:
            print(f"  -> Request failed: {e}, trying next source")
    return None, None


def fetch_for_date(d: date) -> tuple[dict[str, PriceEntry] | None, str | None]:
    """
    Fetch gold prices for a given date.
    - Today: tries historical date-parameterized sources first, then full fallback list.
    - Past dates: tries historical date-parameterized sources only.
    Returns (prices_dict, source_url) on success, or (None, None) on failure. Never raises.
    """
    if d == date.today():
        return _fetch_today()
    return _fetch_historical(d)
