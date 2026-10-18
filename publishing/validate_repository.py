#!/usr/bin/env python3
"""Validate current public contract strictly while preserving earlier published legacy formats.

No historic public data is rewritten or re-issued. Incoming drafts require
confidentiality review BEFORE they enter this already-public GitHub repository.
"""
from __future__ import annotations
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Direct-script entry points otherwise omit the repository root from sys.path.
# Required for importing publishing.news_taxonomy when a batch has news_labels.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("public_validation", ROOT / "publishing/validate_public_batch.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
paths = sorted((ROOT / "public-batches").glob("*/public-batch.json"))
assert paths, "No public batches found"
legacy_count = 0

for path in paths:
    obj = json.loads(path.read_text(encoding="utf-8"))
    day = path.parent.name
    if not re.fullmatch(r"\d{8}", day):
        raise AssertionError(f"Unexpected public date folder: {path}")
    if not isinstance(obj, dict) or not str(obj.get("batch_id", "")).startswith(day + "-"):
        raise AssertionError(f"Invalid batch identity: {path}")
    if not isinstance(obj.get("items"), list):
        raise AssertionError(f"Missing article list: {path}")
    try:
        # After 2026-10-08 the strict formal batch contract is authoritative.
        # The older site used several legacy ID formats; those are already public.
        if day >= "20261008":
            mod.validate_payload(obj)
        else:
            legacy_count += 1
            mod.scan_forbidden_content(obj)
            mod.reject_unknown_fields(obj, mod.TOP_LEVEL_FIELDS, str(path))
            for i, item in enumerate(obj["items"]):
                assert isinstance(item, dict), f"Invalid legacy item in {path}"
                mod.reject_unknown_fields(item, mod.ITEM_FIELDS, f"{path}.items[{i}]")
                mod.require_nonempty_string(item.get("public_id"), f"{path}.items[{i}].public_id")
                mod.require_nonempty_string(item.get("title"), f"{path}.items[{i}].title")
                mod.require_nonempty_string(item.get("content_html"), f"{path}.items[{i}].content_html")
                mod.validate_https_url(item.get("source_url"), f"{path}.items[{i}].source_url")
    except Exception as exc:
        raise RuntimeError(f"Historical public batch incompatible: {path}: {exc}") from exc

print(f"Validated {len(paths)} published batches; {legacy_count} legacy batches retained unchanged.")
