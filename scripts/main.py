"""
Gold Price Scraper with multi-source fallback.
Tries each source in order until one returns data successfully.
"""

import json
from datetime import datetime

import requests

from parsers import (
    HEADERS,
    normalize_prices,
    parse_cafef,
    parse_sjc,
    parse_generic,
)


def fetch_html(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


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


def fetch_with_fallback() -> tuple[list[dict], str]:
    """Try each source in order; return (prices, source_url) on first success."""
    last_error = None
    for url, parser in SOURCES:
        print(f"Trying {url} ...")
        try:
            html = fetch_html(url)
            prices = parser(html)
            if prices:
                print(f"  -> Got {len(prices)} entries")
                return prices, url
            print("  -> Parsed OK but no prices found, trying next source")
        except requests.RequestException as e:
            last_error = e
            print(f"  -> Request failed: {e}, trying next source")

    raise RuntimeError(f"All sources exhausted. Last error: {last_error}")


def save_to_json(prices: list[dict], source_url: str, filename: str = "gold_prices.json") -> None:
    output = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": source_url,
        "prices": prices,
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(prices)} price records to {filename}")


def main():
    try:
        prices, source_url = fetch_with_fallback()
        prices = normalize_prices(prices)
    except RuntimeError as e:
        print(f"Error: {e}")
        return

    print(f"\nSource: {source_url}")
    print(f"Found {len(prices)} gold price entries")

    filename = datetime.now().strftime("%Y%m%d") + "_gold_prices.json"
    save_to_json(prices, source_url, filename)


if __name__ == "__main__":
    main()
