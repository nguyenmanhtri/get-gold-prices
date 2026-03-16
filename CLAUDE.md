# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Run the scraper:**
```bash
python scripts/main.py
```

Note: `scripts/setup.sh` is only for deploying to the Raspberry Pi 5. It is not needed for local development.

## Architecture

This is an OpenClaw skill (`SKILL.md`) that fetches Vietnamese gold prices from the simplize.vn API and outputs a JSON report. All Python code lives in `scripts/`.

**Data flow:**
1. `main.py` — entry point; fetches today's prices from the API, loads historical snapshots from `gold_history.csv`, computes comparisons, and writes `YYYYMMDD_gold_prices.json`. Key functions:
   - `fetch_prices()` — calls the simplize.vn live price API; returns `(prices, source)` or `(None, None)` on failure
   - `load_history(csv_path)` — reads `gold_history.csv` into a `dict` keyed by date string
   - `csv_row_to_snapshot(row, date_str, csv_path)` — converts a CSV row to a `Snapshot`; returns a null-prices snapshot if the date is missing
   - `compute_delta(today_entry, past_entry)` — computes buy/sell diffs and percentages between two `PriceEntry` values
2. `constants.py` — API URLs (`API_URL`, `HISTORY_CHART_URL`), request headers, ticker symbols (`TICKERS`), CSV column names (`CSV_COLUMNS`), and output directory paths
3. `schemas.py` — TypedDict types for the full data model: `GoldPriceReport`, `Snapshot`, `PriceEntry`, `ComparisonDelta`, `GoldTypeComparison`
4. `_scrape_history.py` — standalone utility to pull historical price series from the simplize.vn chart API (OHLCV format) and write `gold_history.csv`. Run manually to refresh the historical dataset.

**Gold types** (`GoldType` enum in `schemas.py`):
- `vang_mieng_sjc` — SJC gold bars (ticker prefix `BTMC:BVV9999`)
- `vang_9999_24k` — 24K/9999 gold rings (ticker prefix `BTMC:RTL9999`)

**Historical data:** `gold_history.csv` (in the output dir) is pre-built by `_scrape_history.py`. Columns: `date`, `vang_mieng_sjc_buy`, `vang_mieng_sjc_sell`, `vang_9999_24k_buy`, `vang_9999_24k_sell`. Prices are in VND per lượng.

**Output schema:** The JSON report has three top-level keys: `generated_at`, `snapshots` (`today`/`7d_ago`/`1y_ago`), and `comparison` (per gold type, per time period: diffs and percentages). If today's fetch fails entirely, `comparison` is `null` and the process exits with code 1.

## Notes on Plugins / Skills

Whenever, u use the `superpower` skills, u can create whatever md files u want, but DO NOT `git add` or `git commit` any of them. I will personally decide what to do with them later.
