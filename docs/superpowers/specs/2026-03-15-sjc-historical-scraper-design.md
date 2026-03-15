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

The `data` array for a ring ticker that has no historical data will be an empty list `[]` — not an error.

---

## Tickers

| Ticker           | Description             | Data availability  |
|------------------|-------------------------|--------------------|
| `SJC:M1L:BUY`   | SJC bar 1 lượng — buy   | Jan 2012 – present |
| `SJC:M1L:SELL`  | SJC bar 1 lượng — sell  | Jan 2012 – present |
| `SJC:T9999:BUY` | SJC ring 99.99 — buy    | Mar 2024 – present |
| `SJC:T9999:SELL`| SJC ring 99.99 — sell   | Mar 2024 – present |

---

## Script

**File:** `get-gold-prices/scripts/scrape_history.py`

**Working directory:** the script must be run from the repo root (`my-openclaw-skills/`). The output path is resolved relative to `__file__` so the cwd does not matter in practice — see Output section below.

**Steps:**
1. Fetch all four tickers with `period=all`. For each ticker:
   a. Call `requests.get(url, headers=..., timeout=30)`.
   b. Call `response.raise_for_status()` to catch HTTP-level errors (4xx/5xx).
   c. Parse the JSON body and check `body["status"] == 200`; if not, raise a `RuntimeError` with the message field.
   d. If `body["data"]` is an empty list, log a warning (`"No data for ticker <X>"`) and continue — this is expected for ring tickers if the API returns nothing.
2. For each non-empty data row `[ts, open, high, low, close, _]`, extract `(ts, close)`. Index 4 is the close price.
3. Convert each Unix timestamp to a `YYYY-MM-DD` date string in **UTC+7 (Asia/Ho_Chi_Minh)** timezone using `datetime.fromtimestamp(ts, tz=ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%Y-%m-%d")`.
4. Accumulate into a single `dict[date_str, dict]` where each inner dict holds the four column values for that month. For each ticker, set only its own column; leave the others untouched so they remain `None`.
5. Sort all dates ascending.
6. Write to CSV with columns: `date, sjc_bar_buy, sjc_bar_sell, sjc_ring_buy, sjc_ring_sell`. Empty cells (missing ring data before Mar 2024) are written as blank strings.
7. Print a summary to stdout: row count per ticker, full date range in the output, output file path.

**Output file:** resolved relative to `__file__` as `Path(__file__).parent / "gold_history.csv"` → `get-gold-prices/scripts/gold_history.csv`.

Ring columns are blank for dates before Mar 2024 — no backfill or interpolation.

---

## Error handling

- HTTP-level errors (4xx/5xx): `raise_for_status()` raises `requests.HTTPError`; let it propagate.
- API-level errors (HTTP 200 but `body["status"] != 200`): raise `RuntimeError(body["message"])`.
- Empty `data` array: log a warning and skip — not a fatal error (expected for ring tickers with limited history).
- No retry logic — the API is reliable; re-run the script on failure.

---

## Dependencies

No new dependencies. Uses `requests` already declared in `requirements.txt`. Uses `zoneinfo` (stdlib, Python 3.9+) for timezone conversion.

---

## Running

```bash
source ~/.local/share/get-gold-prices-skill-venv/bin/activate
python get-gold-prices/scripts/scrape_history.py
deactivate
```

Output is written to `get-gold-prices/scripts/gold_history.csv` regardless of working directory.

---

## Out of scope

- OHLC columns (open, high, low) — only close price is captured
- Other SJC products (5 chỉ, 1 chỉ, nữ trang)
- Incremental updates / append mode
- Scheduling / automation
