#!/usr/bin/env python3
"""Validate existing public batches; incoming content needs approval before any public GitHub write."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("public_validation", ROOT / "publishing/validate_public_batch.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
paths = sorted((ROOT / "public-batches").glob("*/public-batch.json"))
assert paths, "No public batches found"
for path in paths:
    obj = json.loads(path.read_text(encoding="utf-8"))
    mod.validate_payload(obj)
    day = path.parent.name
    assert obj["batch_id"].startswith(day + "-"), f"unexpected batch identity {path}"
    for item in obj["items"]:
        assert item["public_id"].startswith(f"gai-{day}-"), f"article identity mismatch {path}"
print(f"Validated {len(paths)} previously public batches.")
