import os

API_URL = "https://api2.simplize.vn/api/company/commodity/gold/price"
HISTORY_CHART_URL = "https://api2.simplize.vn/api/historical/prices/chart?ticker={ticker}&period=1y"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

TICKERS = {
    "vang_mieng_sjc_buy":  "BTMC:BVV9999:BUY",
    "vang_mieng_sjc_sell": "BTMC:BVV9999:SELL",
    "vang_9999_24k_buy":   "BTMC:RTL9999:BUY",
    "vang_9999_24k_sell":  "BTMC:RTL9999:SELL",
}

CSV_COLUMNS = ["date", "vang_mieng_sjc_buy", "vang_mieng_sjc_sell", "vang_9999_24k_buy", "vang_9999_24k_sell"]
LOCAL_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
PI_OUTPUT_DIR = "/home/frank/.openclaw/workspace"
