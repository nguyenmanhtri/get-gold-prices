"""
Standalone utility to pull historical gold price series from the simplize.vn API
and write a dated CSV covering 2025–2026.
"""
import csv
from datetime import datetime, timezone
from pathlib import Path

import requests

from constants import CSV_COLUMNS, HEADERS, HISTORY_CHART_URL, TICKERS


def _output_path() -> Path:
    if Path.home().name == "frank":
        out_dir = Path("/home/frank/.openclaw/workspace")
    else:
        out_dir = Path(__file__).parent / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / "gold_history.csv"


def fetch_ticker(ticker: str) -> list[dict]:
    url = HISTORY_CHART_URL.format(ticker=ticker)
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


def write_csv(rows: list[dict], filename: Path) -> None:
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
    output = _output_path()
    write_csv(filtered, output)
    print(f"Wrote {len(filtered)} rows to {output}")


if __name__ == "__main__":
    main()
