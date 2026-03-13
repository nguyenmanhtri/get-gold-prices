"""
Gold Price Scraper — fetches today, 7 days ago, and 1 year ago in one run.
Writes a single YYYYMMDD_gold_prices.json with prices and comparisons.
"""
import json
import sys
from datetime import date, datetime, timedelta

from compare import build_comparison
from fetcher import fetch_for_date, one_year_ago
from schemas import GoldPriceReport, Snapshot


def make_snapshot(d: date) -> Snapshot:
    prices, source = fetch_for_date(d)
    return {"date": d.strftime("%Y-%m-%d"), "source": source, "prices": prices}


def save_to_json(report: GoldPriceReport, filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Saved report to {filename}")


def main() -> None:
    today = date.today()
    d7 = today - timedelta(days=7)
    d1y = one_year_ago(today)

    print(f"Fetching prices for: today={today}, 7d_ago={d7}, 1y_ago={d1y}")

    today_snap = make_snapshot(today)
    d7_snap = make_snapshot(d7)
    d1y_snap = make_snapshot(d1y)

    comparison = build_comparison(today_snap, d7_snap, d1y_snap)

    report: GoldPriceReport = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "snapshots": {"today": today_snap, "7d_ago": d7_snap, "1y_ago": d1y_snap},
        "comparison": comparison,
    }

    filename = today.strftime("%Y%m%d") + "_gold_prices.json"
    save_to_json(report, filename)

    if today_snap["prices"] is None:
        print("Error: today's fetch failed — no prices retrieved from any source")
        sys.exit(1)


if __name__ == "__main__":
    main()
