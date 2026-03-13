"""
Date-aware HTTP fetching for gold price sources.
"""
from datetime import date

import requests

from parsers import (
    HEADERS,
    normalize_prices,
    parse_cafef,
    parse_sjc,
    parse_generic,
)
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

# Full source list for today's multi-source fallback (static URLs, no date param).
SOURCES = [
    ("https://cafef.vn/du-lieu/gia-vang-hom-nay/trong-nuoc.chn", parse_cafef),
    ("https://sjc.com.vn/gia-vang-online",                        parse_sjc),
    ("https://www.pnj.com.vn/site/gia-vang",                      parse_generic),
    ("https://doji.vn/gia-vang",                                   parse_generic),
    ("https://webgia.com/gia-vang/sjc/",                           parse_generic),
    ("https://simplize.vn/gia-vang",                               parse_generic),
    ("https://baomoi.com/tien-ich-gia-vang.epi",                   parse_generic),
    ("https://www.24h.com.vn/gia-vang-hom-nay-c425.html",         parse_generic),
    ("https://giavang.org",                                        parse_generic),
    ("https://vneconomy.vn/gia-vang.htm",                          parse_generic),
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


def _fetch_today() -> tuple[dict[str, PriceEntry] | None, str | None]:
    """Try HISTORICAL_SOURCES first (with today's date), then fall back to full SOURCES list."""
    prices, source = _fetch_historical(date.today())
    if prices:
        return prices, source

    for url, parser in SOURCES:
        print(f"Trying {url} ...")
        try:
            html = fetch_html(url)
            raw = parser(html)
            if raw:
                result = to_price_dict(normalize_prices(raw))
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
