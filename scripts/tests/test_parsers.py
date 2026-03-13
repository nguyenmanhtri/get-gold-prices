import pytest
from parsers import categorize, price_to_int, normalize_prices, parse_price, GoldType


class TestCategorize:
    def test_sjc_mieng(self):
        assert categorize("SJC Vàng miếng") == GoldType.SJC_MIENG

    def test_sjc_mieng_lowercase(self):
        assert categorize("vàng miếng sjc") == GoldType.SJC_MIENG

    def test_nhan_excluded_from_sjc(self):
        assert categorize("SJC nhẫn") is None

    def test_vang_9999(self):
        assert categorize("Vàng 9999") == GoldType.VANG_9999

    def test_vang_9999_comma_format(self):
        assert categorize("Vàng 99,99") == GoldType.VANG_9999

    def test_unrecognized_returns_none(self):
        assert categorize("Bạch kim") is None


class TestPriceToInt:
    def test_dot_separated(self):
        assert price_to_int("18.180.000") == 18180000

    def test_comma_separated(self):
        assert price_to_int("18,180,000") == 18180000

    def test_empty_string(self):
        assert price_to_int("") is None

    def test_non_numeric(self):
        assert price_to_int("N/A") is None


class TestParsePrice:
    def test_extracts_price(self):
        assert parse_price("Giá: 18.180.000 VND") == "18.180.000"

    def test_empty_string(self):
        assert parse_price("") == ""

    def test_no_price_in_text(self):
        assert parse_price("Không có dữ liệu") == ""


class TestNormalizePrices:
    def test_deduplicates_same_type(self):
        raw = [
            {"gold_type": "SJC Vàng miếng HCM", "buy_price": "18.000.000", "sell_price": "18.200.000"},
            {"gold_type": "SJC Vàng miếng HN", "buy_price": "18.050.000", "sell_price": "18.250.000"},
        ]
        result = normalize_prices(raw)
        assert len(result) == 1
        assert result[0]["gold_type"] == "vang_mieng_sjc"

    def test_keeps_first_occurrence(self):
        raw = [
            {"gold_type": "SJC Vàng miếng", "buy_price": "18.000.000", "sell_price": "18.200.000"},
            {"gold_type": "Vàng 9999", "buy_price": "17.900.000", "sell_price": "18.100.000"},
        ]
        result = normalize_prices(raw)
        assert len(result) == 2
        types = {r["gold_type"] for r in result}
        assert types == {"vang_mieng_sjc", "vang_9999_24k"}

    def test_skips_unrecognized(self):
        raw = [{"gold_type": "Platinum", "buy_price": "50.000.000", "sell_price": "51.000.000"}]
        result = normalize_prices(raw)
        assert result == []

    def test_converts_prices_to_int(self):
        # normalize_prices keeps buy_price/sell_price keys; rename to buy/sell happens in fetcher.py
        raw = [{"gold_type": "SJC Vàng miếng", "buy_price": "18.180.000", "sell_price": "18.482.000"}]
        result = normalize_prices(raw)
        assert result[0]["buy_price"] == 18180000
        assert result[0]["sell_price"] == 18482000


class TestParseCafef:
    def test_extracts_sjc_mieng_price(self):
        html = """
        <html><body>
          <div id="gia_mua_vao">18.180.000</div>
          <div id="gia_ban_ra">18.482.000</div>
        </body></html>
        """
        from parsers import parse_cafef
        result = parse_cafef(html)
        assert len(result) >= 1
        entry = next(e for e in result if "SJC" in e["gold_type"] or "sjc" in e["gold_type"].lower())
        assert entry["buy_price"] == "18.180.000"
        assert entry["sell_price"] == "18.482.000"


class TestParseSjc:
    def test_extracts_prices_from_table(self):
        html = """
        <html><body>
          <table>
            <tr><td>SJC Vàng miếng</td><td>18.180.000</td><td>18.482.000</td></tr>
          </table>
        </body></html>
        """
        from parsers import parse_sjc
        result = parse_sjc(html)
        assert len(result) == 1
        assert "SJC" in result[0]["gold_type"]
        assert result[0]["buy_price"] == "18.180.000"
        assert result[0]["sell_price"] == "18.482.000"


class TestParseGeneric:
    def test_extracts_gold_row_from_table(self):
        html = """
        <html><body>
          <table>
            <tr><td>Vàng miếng SJC</td><td>18.180.000</td><td>18.482.000</td></tr>
          </table>
        </body></html>
        """
        from parsers import parse_generic
        result = parse_generic(html)
        assert len(result) >= 1
        assert result[0]["buy_price"] == "18.180.000"

    def test_ignores_non_gold_rows(self):
        html = """
        <html><body>
          <table>
            <tr><td>Platinum</td><td>50.000.000</td><td>51.000.000</td></tr>
          </table>
        </body></html>
        """
        from parsers import parse_generic
        result = parse_generic(html)
        assert result == []
