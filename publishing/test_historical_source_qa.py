#!/usr/bin/env python3
"""Regression guard for explicitly reviewed legacy news corrections.

Corrections are narrow, preserve historical public identity, and distinguish
legislative proposal from implemented rules and archival time from later news.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def read(day):
    return json.loads((ROOT / "public-batches" / day / "public-batch.json").read_text(encoding="utf-8"))
cbam = read("20260917")
whirlpool = read("20260919")
assert len(cbam["items"]) == 2 and len(whirlpool["items"]) == 1
assert cbam["batch_id"] == "20260917-0715"
assert whirlpool["batch_id"] == "20260919-0715"
c = next(x for x in cbam["items"] if x["public_id"] == "gai-20260917-002")
w = whirlpool["items"][0]
assert c["event"]["event_key"] == "eu-cbam-expansion-2026"
assert c["event"]["date"] == "2026-09-15"
assert c["source_published_date"] == "2026-09-15"
assert "2025/0419(COD)" in c["content_html"]
assert "洗衣机" in c["content_html"]
assert "仍未确定" in c["content_html"]
assert "不是最终规则已经生效" in c["content_html"] or "并非最终" in c["content_html"]
assert "https://oeil.europarl.europa.eu" in c["content_html"]
assert w["public_id"] == "gai-20260919-001"
assert w["event"]["event_key"] == "whirlpool-italy-fabriano-rd-closure-2026"
assert w["source_published_date"] == "2026-09-18"
assert "/2026/09/18/" in w["source_url"]
assert "sindacati-convocano-unassemblea" in w["source_url"]
assert "正在评估关闭" in w["content_html"]
assert "不是" in w["content_html"] or "不能写作已经关闭" in w["content_html"]
assert "40" in w["content_html"]
assert "补充来源：" in w["content_html"]
print("Historically reviewed CBAM/Whirlpool news corrections are internally consistent.")
