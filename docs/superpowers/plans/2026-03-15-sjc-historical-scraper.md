# SJC Historical Gold Price Scraper Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `scripts/scrape_history.py` that fetches SJC bar and ring historical gold prices from `api.simplize.vn` and writes them to `scripts/gold_history.csv`.

**Architecture:** Single standalone script. Calls four ticker endpoints (`SJC:M1L:BUY`, `SJC:M1L:SELL`, `SJC:T9999:BUY`, `SJC:T9999:SELL`) with `period=all`, merges by date, writes CSV. A companion test file covers all logic using `pytest` and `unittest.mock` to avoid real network calls.

**Tech Stack:** Python 3.9+, `requests`, `zoneinfo` (stdlib), `csv` (stdlib), `pytest`, `unittest.mock`

---

## Chunk 1: Fetch and parse a single ticker response

**Spec:** `docs/superpowers/specs/2026-03-15-sjc-historical-scraper-design.md`

### Task 1: Write and verify the fetch-and-parse function

**Files:**
- Create: `get-gold-prices/scripts/scrape_history.py`
- Create: `get-gold-prices/scripts/test_scrape_history.py`

The script exposes one testable function: `fetch_ticker(ticker: str) -> list[tuple[str, float]]` which returns a list of `(date_str, close_price)` pairs. All network and parsing logic lives here.

---

- [ ] **Step 1: Create `test_scrape_history.py` with a failing test for `fetch_ticker`**

```python
# get-gold-prices/scripts/test_scrape_history.py
from unittest.mock import patch, Mock
from scrape_history import fetch_ticker


def _mock_response(data):
    m = Mock()
    m.raise_for_status.return_value = None
    m.json.return_value = {"status": 200, "message": "Success", "data": data}
    return m


def test_fetch_ticker_returns_date_close_pairs():
    # Unix timestamp 1325350800 = 2012-01-01 in UTC+7
    fake_data = [[1325350800, 4.08e7, 4.51e7, 4.08e7, 4.51e7, None]]
    with patch("scrape_history.requests.get", return_value=_mock_response(fake_data)):
        result = fetch_ticker("SJC:M1L:BUY")
    assert result == [("2012-01-01", 4.51e7)]


def test_fetch_ticker_empty_data_returns_empty_list():
    with patch("scrape_history.requests.get", return_value=_mock_response([])):
        result = fetch_ticker("SJC:T9999:BUY")
    assert result == []


def test_fetch_ticker_raises_on_api_error():
    m = Mock()
    m.raise_for_status.return_value = None
    m.json.return_value = {"status": 500, "message": "Có lỗi xảy ra"}
    with patch("scrape_history.requests.get", return_value=m):
        try:
            fetch_ticker("SJC:M1L:BUY")
            assert False, "expected RuntimeError"
        except RuntimeError as e:
            assert "Có lỗi xảy ra" in str(e)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd get-gold-prices
source ~/.local/share/get-gold-prices-skill-venv/bin/activate
python -m pytest scripts/test_scrape_history.py -v
```

Expected: `ImportError: No module named 'scrape_history'`

- [ ] **Step 3: Create `scrape_history.py` with `fetch_ticker`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest scripts/test_scrape_history.py -v
```

Expected:
```
PASSED test_fetch_ticker_returns_date_close_pairs
PASSED test_fetch_ticker_empty_data_returns_empty_list
PASSED test_fetch_ticker_raises_on_api_error
3 passed
```

- [ ] **Step 5: Commit**

```bash
git add scripts/scrape_history.py scripts/test_scrape_history.py
git commit -m "feat: add fetch_ticker — fetches single ticker history from api.simplize.vn"
```

---

## Chunk 2: Merge tickers and write CSV

### Task 2: Write and verify `merge_tickers` and `write_csv`

**Files:**
- Modify: `get-gold-prices/scripts/scrape_history.py` (add `merge_tickers`, `write_csv`, `main`)
- Modify: `get-gold-prices/scripts/test_scrape_history.py` (add tests for merge and CSV)

---

- [ ] **Step 1: Write failing tests for `merge_tickers`**

Add to `test_scrape_history.py`:

```python
from scrape_history import merge_tickers

COLUMNS = ["sjc_bar_buy", "sjc_bar_sell", "sjc_ring_buy", "sjc_ring_sell"]


def test_merge_tickers_combines_by_date():
    ticker_data = {
        "sjc_bar_buy":  [("2012-01-01", 4.08e7), ("2012-02-01", 4.50e7)],
        "sjc_bar_sell": [("2012-01-01", 4.51e7), ("2012-02-01", 4.60e7)],
        "sjc_ring_buy":  [("2024-03-01", 6.925e7)],
        "sjc_ring_sell": [("2024-03-01", 7.10e7)],
    }
    rows = merge_tickers(ticker_data)
    assert rows[0] == {
        "date": "2012-01-01",
        "sjc_bar_buy": 4.08e7,
        "sjc_bar_sell": 4.51e7,
        "sjc_ring_buy": None,
        "sjc_ring_sell": None,
    }
    assert rows[-1] == {
        "date": "2024-03-01",
        "sjc_bar_buy": None,
        "sjc_bar_sell": None,
        "sjc_ring_buy": 6.925e7,
        "sjc_ring_sell": 7.10e7,
    }


def test_merge_tickers_sorted_ascending():
    ticker_data = {
        "sjc_bar_buy":  [("2012-02-01", 1.0), ("2012-01-01", 2.0)],
        "sjc_bar_sell": [],
        "sjc_ring_buy":  [],
        "sjc_ring_sell": [],
    }
    rows = merge_tickers(ticker_data)
    dates = [r["date"] for r in rows]
    assert dates == sorted(dates)
```

- [ ] **Step 2: Run to verify they fail**

```bash
python -m pytest scripts/test_scrape_history.py::test_merge_tickers_combines_by_date scripts/test_scrape_history.py::test_merge_tickers_sorted_ascending -v
```

Expected: `ImportError` or `AttributeError` — `merge_tickers` not defined yet.

- [ ] **Step 3: Implement `merge_tickers` in `scrape_history.py`**

Add after `fetch_ticker`:

```python
def merge_tickers(
    ticker_data: dict[str, list[tuple[str, float]]]
) -> list[dict]:
    """Merge per-ticker lists into one row per date, sorted ascending."""
    merged: dict[str, dict] = {}
    for col, pairs in ticker_data.items():
        for date_str, close in pairs:
            row = merged.setdefault(date_str, {
                "date": date_str,
                "sjc_bar_buy": None,
                "sjc_bar_sell": None,
                "sjc_ring_buy": None,
                "sjc_ring_sell": None,
            })
            row[col] = close
    return sorted(merged.values(), key=lambda r: r["date"])
```

- [ ] **Step 4: Run merge tests to verify they pass**

```bash
python -m pytest scripts/test_scrape_history.py::test_merge_tickers_combines_by_date scripts/test_scrape_history.py::test_merge_tickers_sorted_ascending -v
```

Expected: `2 passed`

- [ ] **Step 5: Write failing test for `write_csv`**

Add to `test_scrape_history.py`:

```python
import io
from scrape_history import write_csv

def test_write_csv_produces_correct_output():
    rows = [
        {"date": "2012-01-01", "sjc_bar_buy": 40800000.0, "sjc_bar_sell": 45100000.0,
         "sjc_ring_buy": None, "sjc_ring_sell": None},
        {"date": "2024-03-01", "sjc_bar_buy": 69250000.0, "sjc_bar_sell": 71000000.0,
         "sjc_ring_buy": 69250000.0, "sjc_ring_sell": 71000000.0},
    ]
    buf = io.StringIO()
    write_csv(rows, buf)
    buf.seek(0)
    lines = buf.read().splitlines()
    assert lines[0] == "date,sjc_bar_buy,sjc_bar_sell,sjc_ring_buy,sjc_ring_sell"
    assert lines[1] == "2012-01-01,40800000.0,45100000.0,,"
    assert lines[2] == "2024-03-01,69250000.0,71000000.0,69250000.0,71000000.0"
```

- [ ] **Step 6: Run to verify it fails**

```bash
python -m pytest scripts/test_scrape_history.py::test_write_csv_produces_correct_output -v
```

Expected: `ImportError` — `write_csv` not defined yet.

- [ ] **Step 7: Implement `write_csv` in `scrape_history.py`**

Add after `merge_tickers`:

```python
COLUMNS = ["date", "sjc_bar_buy", "sjc_bar_sell", "sjc_ring_buy", "sjc_ring_sell"]


def write_csv(rows: list[dict], dest) -> None:
    """Write merged rows to *dest* (file path or file-like object)."""
    writer = csv.DictWriter(dest, fieldnames=COLUMNS, extrasaction="ignore",
                            lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: ("" if row[k] is None else row[k]) for k in COLUMNS})
```

- [ ] **Step 8: Run write_csv test to verify it passes**

```bash
python -m pytest scripts/test_scrape_history.py::test_write_csv_produces_correct_output -v
```

Expected: `1 passed`

- [ ] **Step 9: Commit**

```bash
git add scripts/scrape_history.py scripts/test_scrape_history.py
git commit -m "feat: add merge_tickers and write_csv"
```

---

## Chunk 3: Wire up `main` and end-to-end smoke test

### Task 3: Add `main()` and run the script for real

**Files:**
- Modify: `get-gold-prices/scripts/scrape_history.py` (add `main`, `if __name__ == "__main__"`)
- Modify: `get-gold-prices/scripts/test_scrape_history.py` (add integration-style test for `main`)

---

- [ ] **Step 1: Write failing test for `main`**

Add to `test_scrape_history.py`:

```python
import tempfile, os
from scrape_history import main

def test_main_writes_csv(tmp_path):
    bar_data   = [[1325350800, 4.08e7, 4.51e7, 4.08e7, 4.51e7, None]]
    ring_data  = []

    side_effects = {
        "SJC:M1L:BUY":   bar_data,
        "SJC:M1L:SELL":  bar_data,
        "SJC:T9999:BUY": ring_data,
        "SJC:T9999:SELL": ring_data,
    }

    def fake_get(url, params, headers, timeout):
        ticker = params["ticker"]
        return _mock_response(side_effects[ticker])

    out_path = tmp_path / "out.csv"
    with patch("scrape_history.requests.get", side_effect=fake_get):
        main(out_path=out_path)

    lines = out_path.read_text().splitlines()
    assert lines[0] == "date,sjc_bar_buy,sjc_bar_sell,sjc_ring_buy,sjc_ring_sell"
    assert len(lines) == 2  # header + 1 data row
    assert "2012-01-01" in lines[1]
```

- [ ] **Step 2: Run to verify it fails**

```bash
python -m pytest scripts/test_scrape_history.py::test_main_writes_csv -v
```

Expected: `ImportError` — `main` not defined yet.

- [ ] **Step 3: Implement `main` in `scrape_history.py`**

Add at the bottom of the file:

```python
def main(out_path: Path | None = None) -> None:
    if out_path is None:
        out_path = Path(__file__).parent / "gold_history.csv"

    ticker_data = {}
    for col, ticker in TICKERS.items():
        pairs = fetch_ticker(ticker)
        ticker_data[col] = pairs
        print(f"  {ticker}: {len(pairs)} rows"
              + (f" ({pairs[0][0]} – {pairs[-1][0]})" if pairs else ""))

    rows = merge_tickers(ticker_data)
    with open(out_path, "w", newline="") as f:
        write_csv(rows, f)

    print(f"\nWrote {len(rows)} rows → {out_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run all tests to verify they pass**

```bash
python -m pytest scripts/test_scrape_history.py -v
```

Expected: all tests pass, no failures.

- [ ] **Step 5: Run the script for real and verify output**

```bash
python scripts/scrape_history.py
```

Expected output (example):
```
  SJC:M1L:BUY: 170 rows (2012-01-01 – 2026-03-01)
  SJC:M1L:SELL: 170 rows (2012-01-01 – 2026-03-01)
  SJC:T9999:BUY: 25 rows (2024-03-01 – 2026-03-01)
  SJC:T9999:SELL: 25 rows (2024-03-01 – 2026-03-01)

Wrote 170 rows → .../scripts/gold_history.csv
```

Spot-check the CSV:
```bash
head -5 scripts/gold_history.csv
tail -3 scripts/gold_history.csv
```

Verify: header row present, first date is `2012-01-01`, ring columns blank until `2024-03-01`, last row is current month.

- [ ] **Step 6: Commit**

```bash
git add scripts/scrape_history.py scripts/test_scrape_history.py
git commit -m "feat: add main() — wires fetch, merge, and CSV write into runnable script"
```
