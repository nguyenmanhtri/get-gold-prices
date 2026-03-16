import csv
import json
import os
import sys
from datetime import datetime, timedelta

import requests

from constants import API_URL, CSV_COLUMNS, HEADERS, LOCAL_OUTPUT_DIR, PI_OUTPUT_DIR
from schemas import ComparisonDelta, GoldPriceReport, GoldType, PriceEntry, Snapshot


def get_output_dir() -> str:
    if os.path.isdir(PI_OUTPUT_DIR):
        return PI_OUTPUT_DIR
    os.makedirs(LOCAL_OUTPUT_DIR, exist_ok=True)
    return LOCAL_OUTPUT_DIR


def fetch_prices() -> tuple[dict[str, PriceEntry] | None, str | None]:
    resp = requests.get(API_URL, params={"period": "1D"}, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    items = resp.json()["data"].get("items", [])

    prices: dict[str, PriceEntry] = {}

    # vang_mieng_sjc: prefer SJC MIENG, fall back to any MIENG
    mieng = [i for i in items if i.get("productType") == "MIENG"]
    item = next((i for i in mieng if i.get("exchange") == "SJC"), mieng[0] if mieng else None)
    if item:
        prices[GoldType.SJC_MIENG.value] = {
            "buy": int(item["priceBuy"]),
            "sell": int(item["priceSell"]),
        }

    # vang_9999_24k: NHAN ring, 24K
    nhan = [i for i in items if i.get("productType") == "NHAN" and i.get("karatType") == "24K"]
    if nhan:
        prices[GoldType.VANG_9999.value] = {
            "buy": int(nhan[0]["priceBuy"]),
            "sell": int(nhan[0]["priceSell"]),
        }

    source = API_URL if prices else None
    return (prices if prices else None, source)


def load_history(csv_path: str) -> dict[str, dict]:
    if not os.path.isfile(csv_path):
        return {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        return {row["date"]: row for row in csv.DictReader(f)}


def csv_row_to_snapshot(row: dict | None, date_str: str, csv_path: str) -> Snapshot:
    if row is None:
        return {"date": date_str, "source": None, "prices": None}
    prices: dict[str, PriceEntry] = {
        GoldType.SJC_MIENG.value: {
            "buy": int(row["vang_mieng_sjc_buy"]),
            "sell": int(row["vang_mieng_sjc_sell"]),
        },
        GoldType.VANG_9999.value: {
            "buy": int(row["vang_9999_24k_buy"]),
            "sell": int(row["vang_9999_24k_sell"]),
        },
    }
    return {"date": date_str, "source": csv_path, "prices": prices}


def compute_delta(today_entry: PriceEntry | None, past_entry: PriceEntry | None) -> ComparisonDelta:
    def delta(t, p):
        if t is None or p is None:
            return None, None
        diff = t - p
        pct = round(diff / p * 100, 2) if p != 0 else None
        return diff, pct

    buy_diff, buy_pct = delta(
        today_entry["buy"] if today_entry else None,
        past_entry["buy"] if past_entry else None,
    )
    sell_diff, sell_pct = delta(
        today_entry["sell"] if today_entry else None,
        past_entry["sell"] if past_entry else None,
    )
    return {"buy_diff": buy_diff, "sell_diff": sell_diff, "buy_pct": buy_pct, "sell_pct": sell_pct}


def append_to_history(
    prices: dict[str, PriceEntry],
    date_str: str,
    csv_path: str,
    history: dict[str, dict],
) -> None:
    if prices is None or date_str in history:
        return
    sjc = prices.get(GoldType.SJC_MIENG.value, {})
    k99 = prices.get(GoldType.VANG_9999.value, {})
    row = {
        "date": date_str,
        "vang_mieng_sjc_buy":  sjc.get("buy"),
        "vang_mieng_sjc_sell": sjc.get("sell"),
        "vang_9999_24k_buy":   k99.get("buy"),
        "vang_9999_24k_sell":  k99.get("sell"),
    }
    write_header = not os.path.isfile(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def main() -> None:
    now = datetime.now()
    prices, source = fetch_prices()

    snapshot: Snapshot = {
        "date": now.strftime("%Y-%m-%d"),
        "source": source,
        "prices": prices,
    }
    report: GoldPriceReport = {
        "generated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "snapshots": {"today": snapshot},
        "comparison": None,
    }

    csv_path = os.path.join(get_output_dir(), "gold_history.csv")
    history = load_history(csv_path)

    d7  = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    d1y = (now - timedelta(days=365)).strftime("%Y-%m-%d")

    snap_7d = csv_row_to_snapshot(history.get(d7),  d7,  csv_path)
    snap_1y = csv_row_to_snapshot(history.get(d1y), d1y, csv_path)

    report["snapshots"]["7d_ago"] = snap_7d
    report["snapshots"]["1y_ago"] = snap_1y

    if prices is not None:
        comparison = {}
        for gold_type in GoldType:
            k = gold_type.value
            today_p = prices.get(k)
            past_7d = snap_7d["prices"].get(k) if snap_7d["prices"] else None
            past_1y = snap_1y["prices"].get(k) if snap_1y["prices"] else None
            comparison[k] = {
                "vs_7d_ago": compute_delta(today_p, past_7d),
                "vs_1y_ago": compute_delta(today_p, past_1y),
            }
        report["comparison"] = comparison
        append_to_history(prices, now.strftime("%Y-%m-%d"), csv_path, history)

    filename = now.strftime("%Y%m%d") + "_gold_prices.json"
    output_path = os.path.join(get_output_dir(), filename)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Saved report to {output_path}")

    if prices is None:
        print("Error: no prices retrieved from API")
        sys.exit(1)


if __name__ == "__main__":
    main()
