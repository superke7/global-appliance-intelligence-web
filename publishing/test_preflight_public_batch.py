#!/usr/bin/env python3
"""Pure safety checks for planned one-repository direct public publishing."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from publishing.preflight_public_batch import PreflightError, prepare

root = Path(__file__).resolve().parents[1]
day = "20261017"
existing = json.loads((root / "public-batches" / day / "public-batch.json").read_text(encoding="utf-8"))
registry = json.loads((root / "config/public-event-registry.json").read_text(encoding="utf-8"))
assert prepare(existing, day, existing, [], registry)[1] == "ALREADY_SYNCED"

incoming = copy.deepcopy(existing)
new_item = copy.deepcopy(existing["items"][0])
new_item["public_id"] = "gai-20261017-999"
new_item["source_url"] = "https://example.org/new-appliance-news-unique-20261017"
new_item["event_action"] = "none"
new_item.pop("event", None)
incoming["items"].append(new_item)

merged, state = prepare(incoming, day, existing, [], registry)
assert state == "APPEND_READY"
assert merged["items"][:-1] == existing["items"]
assert merged["items"][-1] == new_item
assert prepare(incoming, day, None, [], registry)[1] == "CREATE_READY"


def rejects(candidate, previous=existing, history=None):
    try:
        prepare(candidate, day, previous, history or [], registry)
    except (PreflightError, ValueError):
        return
    raise AssertionError("unsafe public batch accepted")

# No changes to already published articles
modified = copy.deepcopy(incoming)
modified["items"][0]["title"] = "Modified article"
rejects(modified)

# Block private notes, even if added in an otherwise valid article
internal = copy.deepcopy(incoming)
internal["items"][-1]["internal_note"] = "private plan"
rejects(internal)
internal_text = copy.deepcopy(incoming)
internal_text["items"][-1]["content_html"] = "Internal use only"
rejects(internal_text)

# No replay of public URLs under a different ID
dup = copy.deepcopy(incoming)
dup["items"][-1]["source_url"] = existing["items"][0]["source_url"]
rejects(dup)

# No duplicate historical ID or URL
history = [{"items": [{"public_id": "gai-20261017-999", "source_url": "https://example.org/older"}]}]
rejects(incoming, history=history)
history = [{"items": [{"public_id": "gai-20260928-001", "source_url": new_item["source_url"]}]}]
rejects(incoming, history=history)

# No publication date/identity mismatch
wrong = copy.deepcopy(incoming)
wrong["batch_id"] = "20261018-0715"
rejects(wrong)

print("Single-repository pre-publication safety checks passed")
