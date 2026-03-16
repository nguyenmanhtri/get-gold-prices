"""
Standalone utility to pull historical gold price series from the simplize.vn API
and write a dated CSV covering 2025–2026.
"""
import csv
from datetime import datetime, timezone

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

TICKERS = {
    "vang_mieng_sjc_buy":  "BTMC:BVV9999:BUY",
    "vang_mieng_sjc_sell": "BTMC:BVV9999:SELL",
    "vang_9999_24k_buy":   "BTMC:RTL9999:BUY",
    "vang_9999_24k_sell":  "BTMC:RTL9999:SELL",
}

CSV_COLUMNS = ["date", "vang_mieng_sjc_buy", "vang_mieng_sjc_sell", "vang_9999_24k_buy", "vang_9999_24k_sell"]
OUTPUT_FILE = "gold_history.csv"


def fetch_ticker(ticker: str) -> list[dict]:
    url = f"https://api2.simplize.vn/api/historical/prices/chart?ticker={ticker}&period=1y"
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    payload = response.json()
    data = payload["data"]

    # The API returns a list of OHLCV arrays: [timestamp_ms, open, high, low, close, volume]
    rows = []
    for entry in data:
        if not isinstance(entry, (list, tuple)) or len(entry) < 5:
            continue
        ts_s = entry[0]
        close = entry[4]
        date_str = datetime.fromtimestamp(ts_s, tz=timezone.utc).strftime("%Y-%m-%d")
        rows.append({"date": date_str, "price": int(close)})
    return rows


def merge_series(series: dict[str, list[dict]]) -> list[dict]:
    merged: dict[str, dict] = {}
    for col, rows in series.items():
        for row in rows:
            d = row["date"]
            if d not in merged:
                merged[d] = {"date": d}
            merged[d][col] = row["price"]
    return list(merged.values())


def filter_dates(rows: list[dict], start: str = "2025-01-01") -> list[dict]:
    return [r for r in rows if r["date"] >= start]


def write_csv(rows: list[dict], filename: str = OUTPUT_FILE) -> None:
    rows_sorted = sorted(rows, key=lambda r: r["date"])
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows_sorted)


def main() -> None:
    series: dict[str, list[dict]] = {}
    for col, ticker in TICKERS.items():
        print(f"Fetching {ticker} ...")
        rows = fetch_ticker(ticker)
        print(f"  -> {len(rows)} data points")
        series[col] = rows

    merged = merge_series(series)
    filtered = filter_dates(merged)
    write_csv(filtered)
    print(f"Wrote {len(filtered)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
