from enum import Enum
from typing import TypedDict


class GoldType(Enum):
    SJC_MIENG = "vang_mieng_sjc"
    VANG_9999 = "vang_9999_24k"


class PriceEntry(TypedDict):
    buy: int | None
    sell: int | None


class Snapshot(TypedDict):
    date: str           # "YYYY-MM-DD"
    source: str | None  # URL that succeeded; None if all sources failed
    prices: dict[str, PriceEntry] | None  # None if fetch failed entirely


class ComparisonDelta(TypedDict):
    buy_diff: int | None    # today.buy - past.buy; None if either value unavailable
    sell_diff: int | None
    buy_pct: float | None   # rounded to 2 decimal places; positive = today is higher
    sell_pct: float | None


class GoldTypeComparison(TypedDict):
    vs_7d_ago: ComparisonDelta
    vs_1y_ago: ComparisonDelta


class GoldPriceReport(TypedDict):
    generated_at: str  # "YYYY-MM-DD HH:MM:SS" local time
    snapshots: dict[str, Snapshot]            # keys: "today", "7d_ago", "1y_ago"
    comparison: dict[str, GoldTypeComparison] | None  # None if today's fetch failed
