"""
Gold price source configuration.

Unit notes:
- Most sources report in VND per lượng (1 lượng = 10 chỉ = 37.5g) → multiplier=1
- webgia.com reports in VND per chỉ → multiplier=10
- 24h.com.vn historical pages report in ngàn đồng (thousands VND) per lượng → multiplier=1000
"""
from datetime import date

from parsers import parse_cafef, parse_sjc, parse_generic


def webgia_url(d: date) -> str:
    return f"https://webgia.com/gia-vang/sjc/{d.strftime('%d-%m-%Y')}.html"


def h24_url(d: date) -> str:
    return f"https://www.24h.com.vn/gia-vang-hom-nay-c425.html?ngaythang={d.strftime('%Y-%m-%d')}"


# Sources with known date-parameterized URL patterns.
# webgia_url → per-chỉ; h24_url → per-chỉ
HISTORICAL_SOURCES = [
    (webgia_url, parse_generic, 10),    # VND per chỉ → ×10
    (h24_url,    parse_generic, 1000),  # ngàn đồng per lượng → ×1000
]

# Full source list for today's multi-source fallback (static URLs, no date param).
# All per-lượng in VND unless noted.
SOURCES = [
    ("https://cafef.vn/du-lieu/gia-vang-hom-nay/trong-nuoc.chn", parse_cafef,   1),    # per-lượng
    ("https://sjc.com.vn/gia-vang-online",                        parse_sjc,     1),    # per-lượng
    ("https://www.pnj.com.vn/site/gia-vang",                      parse_generic, 1),    # per-lượng
    ("https://giavang.doji.vn/trangchu.html",                      parse_generic, 1),    # per-lượng
    ("https://webgia.com/gia-vang/sjc/",                           parse_generic, 10),   # per-chỉ
    ("https://simplize.vn/gia-vang",                               parse_generic, 1),    # per-lượng
    ("https://baomoi.com/tien-ich-gia-vang.epi",                   parse_generic, 1),    # per-lượng
    ("https://www.24h.com.vn/gia-vang-hom-nay-c425.html",         parse_generic, 10),   # per-chỉ
    ("https://giavang.org",                                        parse_generic, 1),    # per-lượng
]
