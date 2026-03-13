"""
Price comparison logic: compute deltas between today and historical snapshots.
"""
from schemas import ComparisonDelta, GoldTypeComparison, PriceEntry, Snapshot


def _delta(today_price: int | None, past_price: int | None) -> tuple[int | None, float | None]:
    if today_price is None or past_price is None or past_price == 0:
        return None, None
    diff = today_price - past_price
    pct = round((diff / past_price) * 100, 2)
    return diff, pct


def _compare_pair(
    today_entry: PriceEntry | None,
    past_entry: PriceEntry | None,
) -> ComparisonDelta:
    if today_entry is None or past_entry is None:
        return {"buy_diff": None, "sell_diff": None, "buy_pct": None, "sell_pct": None}
    buy_diff, buy_pct = _delta(today_entry["buy"], past_entry["buy"])
    sell_diff, sell_pct = _delta(today_entry["sell"], past_entry["sell"])
    return {"buy_diff": buy_diff, "sell_diff": sell_diff, "buy_pct": buy_pct, "sell_pct": sell_pct}


def build_comparison(
    today_snap: Snapshot,
    d7_snap: Snapshot,
    d1y_snap: Snapshot,
) -> dict[str, GoldTypeComparison] | None:
    """
    Build comparison dict keyed by gold types found in today's snapshot.
    Returns None if today's prices are None.
    """
    if today_snap["prices"] is None:
        return None

    d7_prices = d7_snap["prices"] or {}
    d1y_prices = d1y_snap["prices"] or {}
    result = {}
    for gold_type, today_entry in today_snap["prices"].items():
        result[gold_type] = {
            "vs_7d_ago": _compare_pair(today_entry, d7_prices.get(gold_type)),
            "vs_1y_ago": _compare_pair(today_entry, d1y_prices.get(gold_type)),
        }
    return result
