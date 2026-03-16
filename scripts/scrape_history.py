# get-gold-prices/scripts/scrape_history.py
import csv
import warnings
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

BASE_URL = "https://api.simplize.vn/api/historical/prices/chart"
HEADERS = {
    "Referer": "https://simplize.vn/gia-vang",
    "User-Agent": "Mozilla/5.0",
}
TZ_VN = ZoneInfo("Asia/Ho_Chi_Minh")

TICKERS = {
    "sjc_bar_buy":  "SJC:M1L:BUY",
    "sjc_bar_sell": "SJC:M1L:SELL",
    "sjc_ring_buy":  "SJC:T9999:BUY",
    "sjc_ring_sell": "SJC:T9999:SELL",
}


COLUMNS = ["date", "sjc_bar_buy", "sjc_bar_sell", "sjc_ring_buy", "sjc_ring_sell"]


def fetch_ticker(ticker: str) -> list[tuple[str, float]]:
    """Return list of (YYYY-MM-DD, close_price) for *ticker*, all-time."""
    response = requests.get(
        BASE_URL,
        params={"ticker": ticker, "period": "all"},
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()
    body = response.json()
    if body["status"] != 200:
        raise RuntimeError(body["message"])
    data = body["data"]
    if not data:
        warnings.warn(f"No data for ticker {ticker}")
        return []
    results = []
    for row in data:
        ts, close = row[0], row[4]  # row: [timestamp, open, high, low, close, volume]
        date_str = datetime.fromtimestamp(ts, tz=TZ_VN).strftime("%Y-%m-%d")
        results.append((date_str, close))
    return results


def merge_tickers(
    ticker_data: dict[str, list[tuple[str, float]]]
) -> list[dict]:
    """Merge per-ticker lists into one row per date, sorted ascending."""
    merged: dict[str, dict] = {}
    for col, pairs in ticker_data.items():
        for date_str, close in pairs:
            row = merged.setdefault(date_str, {
                "date": date_str,
                "sjc_bar_buy": None,
                "sjc_bar_sell": None,
                "sjc_ring_buy": None,
                "sjc_ring_sell": None,
            })
            row[col] = close
    return sorted(merged.values(), key=lambda r: r["date"])


def write_csv(rows: list[dict], dest) -> None:
    """Write merged rows to *dest* (a writable file-like object)."""
    writer = csv.DictWriter(dest, fieldnames=COLUMNS, extrasaction="ignore",
                            lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: ("" if row[k] is None else row[k]) for k in COLUMNS})


def main(out_path: Path | None = None) -> None:
    if out_path is None:
        out_path = Path(__file__).parent / "gold_history.csv"

    ticker_data = {}
    for col, ticker in TICKERS.items():
        pairs = fetch_ticker(ticker)
        ticker_data[col] = pairs
        print(f"  {ticker}: {len(pairs)} rows"
              + (f" ({pairs[0][0]} – {pairs[-1][0]})" if pairs else ""))

    rows = merge_tickers(ticker_data)
    with open(out_path, "w", newline="") as f:
        write_csv(rows, f)

    print(f"\nWrote {len(rows)} rows → {out_path}")


if __name__ == "__main__":
    main()
