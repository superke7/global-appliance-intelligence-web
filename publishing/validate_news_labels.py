#!/usr/bin/env python3
"""Validate audited, public-only Sheet metadata before consuming it in website pages."""
from __future__ import annotations

import json
import re
from pathlib import Path

from publishing.news_taxonomy import normalize_labels

ROOT = Path(__file__).resolve().parents[1]
LABEL_DIR = ROOT / "config/news-labels"
FILES = sorted(LABEL_DIR.glob("part-*.json"))
FIELDS = {"事件阶段", "国家/地区", "新闻标注", "影响程度", "事件分类"}
assert len(FILES) == 5, "Unexpected number of reviewed historical label files"

published = {}
for path in (ROOT / "public-batches").glob("*/public-batch.json"):
    batch = json.loads(path.read_text(encoding="utf-8"))
    for item in batch["items"]:
        pid = item["public_id"]
        published.setdefault(pid, []).append({"batch": path.parent.name, "source_url": item.get("source_url")})

reused = {pid: entries for pid, entries in published.items() if len(entries) > 1}
duplicates = {pid: entries for pid, entries in reused.items() if len({e["source_url"] for e in entries}) > 1}
print(f"Historical repeated article references: {len(reused)}; conflicting public identities: {len(duplicates)}")
approved = {}
for path in FILES:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert set(data) == {"schema_version", "matched_only", "items"}
    assert data["schema_version"] == "1.0" and data["matched_only"] is True
    assert isinstance(data["items"], dict)
    for pid, row in data["items"].items():
        assert pid not in approved, f"Duplicate archived label for {pid}"
        assert pid in published, f"Unpublished Sheet item cannot be exposed as a label: {pid}"
        assert pid not in duplicates, f"Ambiguous duplicate ID cannot have a single label: {pid}"
        assert set(row) == FIELDS, f"Non-public Sheet column leaked: {pid}"
        for value in row.values():
            assert isinstance(value, str) and value.strip(), f"Empty field: {pid}"
            assert len(value) < 600, f"Unusually long field: {pid}"
            assert not re.search(r"(?i)github_pat_|ghp_|PRIVATE KEY|仅供内部|内部机密|海尔内部|intranet|hwork", value), (
                f"Potentially confidential label: {pid}"
            )
        output = normalize_labels(row)
        assert output["tags"]["geographies"], f"Unknown geography: {pid}"
        approved[pid] = output

print(json.dumps({
    "distinct_public_ids": len(published),
    "published_articles": sum(len(v) for v in published.values()),
    "safely_matched_labels": len(approved),
    "published_without_reviewed_labels": sum(len(v) for v in published.values()) - len(approved),
    "status": "ok",
}, ensure_ascii=False))
