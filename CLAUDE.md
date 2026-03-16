# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Run the scraper:**
```bash
python scripts/main.py
```

Note: `scripts/setup.sh` is only for deploying to the Raspberry Pi 5. It is not needed for local development.

## Architecture

This is an OpenClaw skill (`SKILL.md`) that scrapes Vietnamese gold prices from multiple websites and outputs a JSON report. All Python code lives in `scripts/`.

**Data flow:**
1. `main.py` — entry point; fetches prices for today, 7 days ago, and 1 year ago, then writes `YYYYMMDD_gold_prices.json`
2. `fetcher.py` — date-aware HTTP fetching with fallback logic:
   - Today: tries `HISTORICAL_SOURCES` (date-parameterized URLs) first, falls back to full `SOURCES` list
   - Past dates: tries `HISTORICAL_SOURCES` only
3. `constants.py` — source registry: `HISTORICAL_SOURCES` (date-parameterized) and `SOURCES` (static URLs for today). Each entry is `(url_or_url_fn, parser_fn, multiplier)` where `multiplier` normalizes prices to VND per lượng
4. `parsers.py` — BeautifulSoup parsers (`parse_cafef`, `parse_sjc`, `parse_generic`) plus `normalize_prices()` which deduplicates and maps raw strings to `GoldType` enum values
5. `compare.py` — computes buy/sell diffs and percentage changes between today and historical snapshots
6. `schemas.py` — TypedDict types for the full data model: `GoldPriceReport`, `Snapshot`, `PriceEntry`, `ComparisonDelta`, `GoldTypeComparison`
7. `scrape_history.py` — standalone utility to pull all-time historical price series from the simplize.vn API (OHLCV format, indexed by ticker like `SJC:M1L:BUY`)

**Gold types** (`GoldType` enum in `schemas.py`):
- `vang_mieng_sjc` — SJC gold bars
- `vang_9999_24k` — 24K/9999 gold rings

**Unit normalization:** Sources report in different units; `multiplier` in the source registry converts everything to VND per lượng before storage. webgia.com uses per-chỉ (×10), 24h.com.vn historical pages use ngàn đồng/lượng (×1000).

**Output schema:** The JSON report has three top-level keys: `generated_at`, `snapshots` (`today`/`7d_ago`/`1y_ago`), and `comparison` (per gold type, per time period: diffs and percentages). If today's fetch fails entirely, `comparison` is `null` and the process exits with code 1.

## Notes on Plugins / Skills

Whenever, u use the `superpower` skills, u can create whatever md files u want, but DO NOT `git add` or `git commit` any of them. I will personally decide what to do with them later.
