"""
Gold Price Scraper with multi-source fallback.
Tries each source in order until one returns data successfully.
"""

import json
import re
from datetime import datetime
from enum import Enum

import requests
from bs4 import BeautifulSoup


class GoldType(Enum):
    SJC_MIEN = "vang_mien_sjc"
    VANG_9999 = "vang_9999_24k"


def categorize(gold_type_str: str) -> GoldType | None:
    s = gold_type_str.lower()
    if "sjc" in s and "nhẫn" not in s:
        return GoldType.SJC_MIEN
    if "miếng" in s and "nhẫn" not in s:
        return GoldType.SJC_MIEN
    if "9999" in s or "99,99" in s or "99.99" in s:
        return GoldType.VANG_9999
    return None


def price_to_int(price_str: str) -> int | None:
    if not price_str:
        return None
    cleaned = price_str.replace(".", "").replace(",", "")
    return int(cleaned) if cleaned.isdigit() else None


def normalize_prices(prices: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for entry in prices:
        category = categorize(entry["gold_type"])
        if category is None or category in seen:
            continue
        seen.add(category)
        result.append({
            "gold_type": category.value,
            "buy_price": price_to_int(entry["buy_price"]),
            "sell_price": price_to_int(entry["sell_price"]),
        })
    return result

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def fetch_html(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


PRICE_PATTERN = re.compile(r"\b\d{1,3}(?:[.,]\d{3})+\b")


def parse_price(price_text: str) -> str:
    if not price_text:
        return ""
    match = PRICE_PATTERN.search(price_text)
    return match.group(0) if match else ""


# ---------------------------------------------------------------------------
# Site-specific parsers
# ---------------------------------------------------------------------------

def parse_cafef(html: str) -> list[dict]:
    """Parse cafef.vn gold prices."""
    soup = BeautifulSoup(html, "html.parser")
    prices = []

    buy_elem = soup.find("div", id="gia_mua_vao")
    sell_elem = soup.find("div", id="gia_ban_ra")
    if buy_elem or sell_elem:
        buy_price = parse_price(buy_elem.get_text()) if buy_elem else ""
        sell_price = parse_price(sell_elem.get_text()) if sell_elem else ""
        if buy_price or sell_price:
            prices.append({
                "gold_type": "SJC Vàng miếng",
                "buy_price": buy_price,
                "sell_price": sell_price,
            })

    buy_ring_elem = soup.find("div", id="gia_mua_vao_nhan")
    sell_ring_elem = soup.find("div", id="gia_ban_ra_nhan")
    if buy_ring_elem or sell_ring_elem:
        buy_price = parse_price(buy_ring_elem.get_text()) if buy_ring_elem else ""
        sell_price = parse_price(sell_ring_elem.get_text()) if sell_ring_elem else ""
        if buy_price or sell_price:
            prices.append({
                "gold_type": "Vàng nhẫn 9999",
                "buy_price": buy_price,
                "sell_price": sell_price,
            })

    tables = soup.find_all("table", class_="content_loai_gia_vang")
    for table in tables:
        region = "Unknown"
        parent_container = table.find_parent("div")
        if parent_container:
            title_elem = parent_container.find_previous_sibling("div", class_="title_loai_gia")
            if title_elem:
                region = title_elem.get_text(strip=True)

        for row in table.find_all("tr"):
            name_cell = row.find("td", class_="content_item_name_loai_vang")
            buy_cell = row.find("td", class_="content_item_gia_mua_loai_vang")
            sell_cell = row.find("td", class_="content_item_gia_ban_loai_vang")

            if not name_cell:
                continue

            span = name_cell.find("span")
            gold_type = span.get_text(strip=True) if span else name_cell.get_text(strip=True)

            buy_div = buy_cell.find("div", class_="item_gia_mua") if buy_cell else None
            sell_div = sell_cell.find("div", class_="item_gia_ban") if sell_cell else None

            buy_price = parse_price(buy_div.get_text()) if buy_div else ""
            sell_price = parse_price(sell_div.get_text()) if sell_div else ""

            if not gold_type or (not buy_price and not sell_price):
                continue

            prices.append({
                "gold_type": gold_type,
                "buy_price": buy_price,
                "sell_price": sell_price,
            })

    return prices


def parse_sjc(html: str) -> list[dict]:
    """Parse sjc.com.vn gold prices."""
    soup = BeautifulSoup(html, "html.parser")
    prices = []

    for row in soup.select("table tr"):
        cells = row.find_all("td")
        if len(cells) >= 3:
            gold_type = cells[0].get_text(strip=True)
            buy_price = parse_price(cells[1].get_text())
            sell_price = parse_price(cells[2].get_text())
            if gold_type and (buy_price or sell_price):
                prices.append({
                    "gold_type": gold_type,
                    "buy_price": buy_price,
                    "sell_price": sell_price,
                })

    return prices


def parse_generic(html: str) -> list[dict]:
    """
    Generic parser: scans all tables for rows that look like gold prices
    (contain Vietnamese gold keywords and at least two numeric price-like values).
    """
    GOLD_KEYWORDS = re.compile(
        r"vàng|gold|sjc|pnj|doji|9999|24k|18k|nhẫn|miếng", re.IGNORECASE
    )

    soup = BeautifulSoup(html, "html.parser")
    prices = []

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            if len(cells) < 2:
                continue

            row_text = " ".join(cells)
            if not GOLD_KEYWORDS.search(row_text):
                continue

            numeric_cells = [c for c in cells if PRICE_PATTERN.search(c)]
            if len(numeric_cells) < 1:
                continue

            # First non-numeric cell is the gold type; first two numeric cells are buy/sell
            name = next((c for c in cells if not PRICE_PATTERN.search(c) and c), cells[0])
            buy_price = parse_price(numeric_cells[0]) if len(numeric_cells) > 0 else ""
            sell_price = parse_price(numeric_cells[1]) if len(numeric_cells) > 1 else ""

            prices.append({
                "gold_type": name,
                "buy_price": buy_price,
                "sell_price": sell_price,
            })

    return prices


# ---------------------------------------------------------------------------
# Source registry: ordered list of (url, parser) to try in sequence
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

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

    raise RuntimeError(
        f"All sources exhausted. Last error: {last_error}"
    )


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

    print("\nPreview of scraped data:")
    for price in prices[:5]:
        print(f"  {price['gold_type']}: Buy={price['buy_price']}, Sell={price['sell_price']}")
    if len(prices) > 5:
        print(f"  ... and {len(prices) - 5} more entries")

    filename = datetime.now().strftime("%Y%m%d") + "_gold_prices.json"
    save_to_json(prices, source_url, filename)


if __name__ == "__main__":
    main()

