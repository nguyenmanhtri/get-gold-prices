# SJC Historical Gold Price Scraper — Design Spec

**Date:** 2026-03-15
**Status:** Approved

---

## Overview

A standalone Python script that scrapes historical SJC gold price data (bar and ring) from the `api.simplize.vn` chart API and writes it to a CSV file. It lives alongside the existing `get-gold-prices` skill scripts and reuses the same virtual environment.

---

## Data Source

**API endpoint:**
```
GET https://api.simplize.vn/api/historical/prices/chart
  ?ticker=<TICKER>
  &period=all
```

**Headers required:**
- `Referer: https://simplize.vn/gia-vang`
- `User-Agent: Mozilla/5.0`

**Response format:**
```json
{
  "status": 200,
  "data": [
    [unix_timestamp, open, high, low, close, null],
    ...
  ]
}
```

Each row is a monthly candle. Prices are in VND per lượng (1 lượng = 37.5g).

---

## Tickers

| Ticker          | Description              | Data availability |
|-----------------|--------------------------|-------------------|
| `SJC:M1L:BUY`  | SJC bar 1 lượng — buy    | Jan 2012 – present |
| `SJC:M1L:SELL` | SJC bar 1 lượng — sell   | Jan 2012 – present |
| `SJC:T9999:BUY` | SJC ring 99.99 — buy    | Mar 2024 – present |
| `SJC:T9999:SELL`| SJC ring 99.99 — sell   | Mar 2024 – present |

---

## Script

**File:** `get-gold-prices/scripts/scrape_history.py`

**Steps:**
1. Fetch all four tickers with `period=all`
2. For each response, extract `[timestamp, close]` from each row (index 0 and 4)
3. Convert Unix timestamp → `YYYY-MM-DD` date string
4. Merge into a single dict keyed by date
5. Write to CSV with columns: `date, sjc_bar_buy, sjc_bar_sell, sjc_ring_buy, sjc_ring_sell`
6. Print a summary: number of rows per ticker, date range, output path

**Output file:** `get-gold-prices/scripts/gold_history.csv`

Ring columns are empty (blank) for dates before Mar 2024 — no backfill or interpolation.

---

## Error handling

- Non-200 HTTP responses raise an exception with the status code
- Empty `data` array logs a warning but doesn't abort (ring may have less data)
- No retry logic — the API is reliable; if it fails, re-run the script

---

## Dependencies

No new dependencies. Uses `requests` already declared in `requirements.txt`.

---

## Running

```bash
source ~/.local/share/get-gold-prices-skill-venv/bin/activate
python get-gold-prices/scripts/scrape_history.py
deactivate
```

---

## Out of scope

- OHLC columns (open, high, low) — only close price is captured
- Other SJC products (5 chỉ, 1 chỉ, nữ trang)
- Incremental updates / append mode
- Scheduling / automation
