# get-gold-prices/scripts/test_scrape_history.py
import io
import pytest
from unittest.mock import patch, Mock
from scrape_history import fetch_ticker, merge_tickers, write_csv, main


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
        with pytest.raises(RuntimeError, match="Có lỗi xảy ra"):
            fetch_ticker("SJC:M1L:BUY")


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
    assert len(lines) == 2  # header + 1 data row (bar_data and ring_data share same timestamp → one merged row)
    assert "2012-01-01" in lines[1]
