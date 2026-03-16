import json
import os
import sys
from datetime import datetime

import requests

from constants import API_URL, HEADERS, LOCAL_OUTPUT_DIR, PI_OUTPUT_DIR
from schemas import GoldPriceReport, GoldType, PriceEntry, Snapshot


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
