#!/usr/bin/env python3
"""Protect browsing facets, exact Sheet descriptions and optional future label schema."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from publishing.news_taxonomy import normalize_labels
from publishing.validate_public_batch import ValidationError, validate_payload

ROOT = Path(__file__).resolve().parents[1]
archived = json.loads((ROOT / "config/news-labels/part-05.json").read_text(encoding="utf-8"))["items"]
labels = archived["gai-20261017-001"]
normalized = normalize_labels(labels)
assert normalized["raw"]["事件阶段"] == labels["事件阶段"]
assert normalized["tags"]["geographies"] == ["欧盟", "中国"]
batch = json.loads((ROOT / "public-batches/20261017/public-batch.json").read_text(encoding="utf-8"))
candidate = copy.deepcopy(batch)
candidate["items"][0]["news_labels"] = labels
validate_payload(candidate)
unsafe = copy.deepcopy(candidate)
unsafe["items"][0]["news_labels"]["内部负责人"] = "secret"
try:
    validate_payload(unsafe)
except ValidationError:
    pass
else:
    raise AssertionError("Unapproved extra field was permitted")

built = ROOT / "_site"
news_page = (built / "news.html").read_text(encoding="utf-8")
article_page = (built / "articles/gai-20261017-001/index.html").read_text(encoding="utf-8")
assert "新闻快速筛选" in news_page
assert 'data-filter="news_mark"' in news_page
assert 'data-filter="geo"' in news_page
assert "符合条件 " in news_page
assert "事件阶段" in article_page and "影响程度" in article_page
assert labels["事件阶段"] in article_page
assert labels["影响程度"] in article_page
assert "news.html?" in article_page

# Inspect rendered HTML, not just the Python helper: this catches mismatches
# between the filter dropdown and the article's data-geos attributes.
from html.parser import HTMLParser


class BrowseArticleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = None
        self.entries = {}

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "article" and "browse-item" in data.get("class", "").split():
            self.active = data
        elif self.active is not None and tag == "a" and data.get("href", "").startswith("articles/"):
            identifier = data["href"].split("/")[1]
            self.entries[identifier] = self.active

    def handle_endtag(self, tag):
        if tag == "article":
            self.active = None


parser = BrowseArticleParser()
parser.feed(news_page)

# Existing Oct 12 French article has only France/China as raw geographical
# labels; it must now match both EU and Europe when the browser is filtered.
france = parser.entries["gai-20261012-005"]
assert "欧盟" in france["data-geos"].split("|")
assert "欧洲" in france["data-geos"].split("|")
assert "法国" in france["data-geos"].split("|")

# A UK-only story must not be categorized as EU-related.
uk = parser.entries["gai-20261012-015"]
assert "英国" in uk["data-geos"].split("|")
assert "欧洲" in uk["data-geos"].split("|")
assert "欧盟" not in uk["data-geos"].split("|")

vietnam = parser.entries["gai-20261009-003"]
assert "东盟" in vietnam["data-geos"].split("|")
assert "东南亚" in vietnam["data-geos"].split("|")
mexico = parser.entries["gai-20261013-003"]
assert "北美" in mexico["data-geos"].split("|")
assert "拉美" in mexico["data-geos"].split("|")
assert "南美" not in mexico["data-geos"].split("|")
assert '<option value="欧盟">' in news_page
assert '<option value="东盟">' in news_page
assert '<option value="北美">' in news_page
assert '地区' in news_page and "不代表该国新闻属于欧盟层面政策" in news_page


# Seven new historic matches are matched by original source (not copied/shifted NEWS IDs).
# Assert the real built article data attributes reflect the reviewed Sheet labels.
assert "gai-20260820-001" in parser.entries
assert "欧盟" in parser.entries["gai-20260820-001"]["data-geos"].split("|")
assert "美国" not in parser.entries["gai-20260820-001"]["data-geos"].split("|")
assert "美国" in parser.entries["gai-20260820-002"]["data-geos"].split("|")
assert "欧盟" not in parser.entries["gai-20260820-002"]["data-geos"].split("|")
assert parser.entries["gai-20260820-002"]["data-impact"] == "高"
assert parser.entries["gai-20260916-001"]["data-stage"] == "已生效/投产"
assert parser.entries["gai-20260916-002"]["data-stage"] == "已宣布待实施"
assert parser.entries["gai-20260728-004"]["data-category"] == "市场与渠道"
assert parser.entries["gai-20261001-002"]["data-impact"] == "高"


# Correctly link the six validated historical Sheet items to their original public
# article identity; do not recreate article IDs, modify RSS, or derive wrong regions.
for public_id in (
    "gai-20260917-002", "gai-20260919-001", "gai-20260922-002",
    "gai-20260923-001", "gai-20260923-002", "gai-20261002-003"
):
    assert public_id in parser.entries, "Historic article lost: " + public_id
    assert parser.entries[public_id]["data-news-mark"] == "历史补录"

assert parser.entries["gai-20260917-002"]["data-stage"] == "谈判磋商"
assert parser.entries["gai-20260917-002"]["data-impact"] == "高"
assert "欧盟" in parser.entries["gai-20260917-002"]["data-geos"].split("|")
assert parser.entries["gai-20260919-001"]["data-stage"] == "已宣布待实施"
assert "欧洲" in parser.entries["gai-20260919-001"]["data-geos"].split("|")
assert parser.entries["gai-20260922-002"]["data-category"] == "制造与产能"
assert "亚洲" in parser.entries["gai-20260922-002"]["data-geos"].split("|")
assert parser.entries["gai-20260923-001"]["data-stage"] == "推进中"
assert "印度" in parser.entries["gai-20260923-001"]["data-geos"].split("|")
assert parser.entries["gai-20260923-002"]["data-stage"] == "已生效/投产"
assert "欧盟" in parser.entries["gai-20260923-002"]["data-geos"].split("|")
assert parser.entries["gai-20261002-003"]["data-stage"] == "规划拟议"
assert "法国" in parser.entries["gai-20261002-003"]["data-geos"].split("|")
assert "欧盟" in parser.entries["gai-20261002-003"]["data-geos"].split("|")

print("Public faceted browser, full original labels, optional schema and private-field rejection verified.")
