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
        ts, close = row[0], row[4]
        date_str = datetime.fromtimestamp(ts, tz=TZ_VN).strftime("%Y-%m-%d")
        results.append((date_str, close))
    return results
