#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH_ROOT = ROOT / "public-batches"
OUT = ROOT / "config" / "public-event-registry.json"

events: dict[str, dict[str, str]] = {}
for path in sorted(BATCH_ROOT.glob("*/public-batch.json")):
    payload = json.loads(path.read_text(encoding="utf-8"))
    for item in payload.get("items", []):
        action = item.get("event_action")
        event = item.get("event")
        if action not in {"create", "update"} or not isinstance(event, dict):
            continue
        title = str(event.get("title", "")).strip()
        key = str(event.get("event_key", "")).strip()
        date = str(event.get("date", "")).strip()
        if not title or not key or not date:
            raise SystemExit(f"invalid event registry source in {path}")
        candidate = {"event_key": key, "date": date}
        prior = events.get(title)
        if prior:
            if prior["event_key"] != key:
                raise SystemExit(
                    f"public event key conflict for {title!r}: {prior['event_key']!r} vs {key!r} in {path}"
                )
            # Historical payloads occasionally changed event.date while keeping
            # the same stable event key/title. Use the earliest observed date
            # as the canonical registry date instead of treating this as a key
            # identity conflict.
            if date < prior["date"]:
                prior["date"] = date
        else:
            events[title] = candidate

out = {
    "schema_version": "1.0",
    "source": "derived from public-batches/*/public-batch.json",
    "events": dict(sorted(events.items())),
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"wrote {OUT.relative_to(ROOT)} with {len(events)} events")
