"""Мэдээний эх сурвалжууд — тогтмол жагсаалт (хэрэглэгч URL өгөхгүй тул SSRF эрсдэлгүй).

1212.mn (Үндэсний статистикийн хороо): RSS байхгүй, /api/articles нь robots.txt-ээр ботод хориотой.
Тиймээс ҮСХ-ноос зөвшөөрөл (өгөгдөл солилцох гэрээ) авсны дараа NSO_API_ENABLED=1 тохируулж асаана.
Тэр хүртэл ҮСХ-ны тухай мэдээг Google News-ээр (нийтэд санал болгосон RSS) дамжуулан харуулна.
"""
import os

GN = "https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={gl}:{lang}"

SOURCES = {
    "nso": {"name": "Үндэсний статистикийн хороо (1212.mn)", "kind": "nso_api", "lang": "mn", "home": "https://www.1212.mn",
            "url": "https://www.1212.mn/api/articles?page=1&pageSize=15&lng=mn&type=latest",
            "enabled": lambda: os.getenv("NSO_API_ENABLED") == "1", "trusted_mn": True},
    "nso_news": {"name": "ҮСХ-ны тухай мэдээ (Google News)", "kind": "rss", "lang": "mn", "home": "https://www.1212.mn",
                 "url": GN.format(q="%22%D2%AE%D0%BD%D0%B4%D1%8D%D1%81%D0%BD%D0%B8%D0%B9+%D1%81%D1%82%D0%B0%D1%82%D0%B8%D1%81%D1%82%D0%B8%D0%BA%D0%B8%D0%B9%D0%BD+%D1%85%D0%BE%D1%80%D0%BE%D0%BE%22",
                                  hl="mn", gl="MN", lang="mn"), "trusted_mn": True},
    "google_en": {"name": "Google News · Mongolia", "kind": "rss", "lang": "en", "home": "https://news.google.com",
                  "url": GN.format(q="Mongolia", hl="en-US", gl="US", lang="en")},
    "ikon": {"name": "ikon.mn", "kind": "rss", "lang": "mn", "home": "https://www.ikon.mn",
             "url": "https://www.ikon.mn/rss", "trusted_mn": True},
    "google_mn": {"name": "Google News · Монгол (олон хэл)", "kind": "rss", "lang": "mn", "home": "https://news.google.com",
                  "url": GN.format(q="%D0%9C%D0%BE%D0%BD%D0%B3%D0%BE%D0%BB", hl="mn", gl="MN", lang="mn")},
    "aljazeera": {"name": "Al Jazeera", "kind": "rss", "lang": "en", "home": "https://www.aljazeera.com",
                  "url": "https://www.aljazeera.com/xml/rss/all.xml"},
    "bbc": {"name": "BBC News · Asia", "kind": "rss", "lang": "en", "home": "https://www.bbc.com",
            "url": "https://feeds.bbci.co.uk/news/world/asia/rss.xml"},
    "diplomat": {"name": "The Diplomat · Central Asia", "kind": "rss", "lang": "en", "home": "https://thediplomat.com",
                 "url": "https://thediplomat.com/regions/central-asia/feed/"},
}


def enabled_sources():
    return {k: s for k, s in SOURCES.items() if s.get("enabled", lambda: True)()}
