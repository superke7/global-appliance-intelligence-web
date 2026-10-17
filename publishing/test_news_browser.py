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
print("Public faceted browser, full original labels, optional schema and private-field rejection verified.")
