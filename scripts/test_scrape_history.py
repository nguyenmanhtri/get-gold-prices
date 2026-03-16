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
    import pytest
    m = Mock()
    m.raise_for_status.return_value = None
    m.json.return_value = {"status": 500, "message": "Có lỗi xảy ra"}
    with patch("scrape_history.requests.get", return_value=m):
        with pytest.raises(RuntimeError, match="Có lỗi xảy ra"):
            fetch_ticker("SJC:M1L:BUY")
