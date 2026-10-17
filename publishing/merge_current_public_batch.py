#!/usr/bin/env python3
"""Append new items to the current Beijing-day public batch without mutating existing items."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_KEYS = {"ref", "source", "tracking"}


class MergeError(ValueError):
    pass


def canonical_url(value: str) -> str:
    parsed = urlsplit(value)
    query = []
    for key, val in parse_qsl(parsed.query, keep_blank_values=True):
        lower = key.lower()
        if lower.startswith("utm_") or lower in TRACKING_KEYS:
            continue
        query.append((key, val))
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, urlencode(query), ""))


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise MergeError(f"{path}: payload must be an object")
    return data


def historical_indexes(root: Path, exclude: Path) -> tuple[set[str], set[str]]:
    ids: set[str] = set()
    urls: set[str] = set()
    if not root.exists():
        return ids, urls
    for path in root.glob("*/public-batch.json"):
        try:
            if path.resolve() == exclude.resolve():
                continue
            payload = load(path)
        except (OSError, json.JSONDecodeError, MergeError):
            continue
        for item in payload.get("items", []):
            if not isinstance(item, dict):
                continue
            pid = item.get("public_id")
            url = item.get("source_url")
            if isinstance(pid, str) and pid:
                ids.add(pid)
            if isinstance(url, str) and url:
                urls.add(canonical_url(url))
    return ids, urls


def merge(existing: dict, incoming: dict, day: str, history_root: Path, existing_path: Path) -> tuple[dict, dict]:
    for field in ("schema_version", "batch_id", "target_publish_at_bjt"):
        if incoming.get(field) != existing.get(field):
            raise MergeError(f"incoming {field} must match existing current-day batch")
    if existing.get("batch_id") != f"{day}-0715":
        raise MergeError("existing batch_id does not match current day")

    existing_items = existing.get("items")
    incoming_items = incoming.get("items")
    if not isinstance(existing_items, list) or not isinstance(incoming_items, list):
        raise MergeError("items must be arrays")

    by_id = {}
    urls = set()
    for item in existing_items:
        if not isinstance(item, dict):
            raise MergeError("existing item must be an object")
        pid = item.get("public_id")
        url = item.get("source_url")
        if isinstance(pid, str):
            by_id[pid] = item
        if isinstance(url, str) and url:
            urls.add(canonical_url(url))

    historical_ids, historical_urls = historical_indexes(history_root, existing_path)
    added = []
    skipped_identical = []
    skipped_historical = []

    for item in incoming_items:
        if not isinstance(item, dict):
            raise MergeError("incoming item must be an object")
        pid = item.get("public_id")
        url = item.get("source_url")
        if not isinstance(pid, str) or not pid.startswith(f"gai-{day}-"):
            raise MergeError("supplemental public_id must use the current Beijing ingestion date")

        prior = by_id.get(pid)
        if prior is not None:
            if prior != item:
                raise MergeError(f"public_id conflict for {pid}; existing items are immutable")
            skipped_identical.append(pid)
            continue
        if pid in historical_ids:
            raise MergeError(f"public_id {pid} already exists in a historical batch")

        canon = canonical_url(url) if isinstance(url, str) and url else ""
        if canon and canon in urls:
            skipped_identical.append(pid)
            continue
        if canon and canon in historical_urls:
            skipped_historical.append(pid)
            continue

        added.append(item)
        by_id[pid] = item
        if canon:
            urls.add(canon)

    merged = dict(existing)
    merged["generated_at_bjt"] = incoming.get("generated_at_bjt", existing.get("generated_at_bjt"))
    merged["items"] = [*existing_items, *added]

    summary = {
        "status": "appended" if added else "no_change",
        "added": len(added),
        "existing": len(existing_items),
        "total": len(merged["items"]),
        "skipped_identical": skipped_identical,
        "skipped_historical": skipped_historical,
    }
    return merged, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--existing", type=Path, required=True)
    parser.add_argument("--incoming", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--day", required=True)
    parser.add_argument("--history-root", type=Path, default=Path("public-batches"))
    args = parser.parse_args()

    try:
        existing = load(args.existing)
        incoming = load(args.incoming)
        merged, summary = merge(existing, incoming, args.day, args.history_root, args.existing)
    except (OSError, json.JSONDecodeError, MergeError) as exc:
        raise SystemExit(f"Current-day public batch merge failed: {exc}")

    args.output.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
