#!/usr/bin/env python3
"""Preflight an already-approved batch BEFORE any write to the public GitHub repo.

This local CLI is a deterministic second check; it does not create a private
review environment and cannot replace upstream factual/confidentiality QA.
Run it with an incoming JSON outside the public repository's Git history.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
BATCH_ROOT = ROOT / "public-batches"
REGISTRY_PATH = ROOT / "config/public-event-registry.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load public checker: " + str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = load_module("public_contract_checker", ROOT / "publishing/validate_public_batch.py")
merger = load_module("public_append_merger", ROOT / "publishing/merge_current_public_batch.py")


class PreflightError(ValueError):
    pass


def normalize_url(url: str) -> str:
    return merger.canonical_url(url)


def history_indexes(history: list[dict]) -> tuple[set[str], set[str]]:
    ids: set[str] = set()
    urls: set[str] = set()
    for batch in history:
        for article in batch.get("items", []):
            pid = article.get("public_id")
            url = article.get("source_url")
            if pid:
                ids.add(pid)
            if url:
                urls.add(normalize_url(url))
    return ids, urls


def verify_event_identity(new_items: list[dict], registry: dict) -> None:
    """Never silently redefine a published event's stable title/key pair."""
    by_title = {}
    by_key = {}
    for title, val in registry.get("events", {}).items():
        if not isinstance(val, dict) or not isinstance(val.get("event_key"), str):
            raise PreflightError("invalid public event registry")
        by_title[title] = val["event_key"]
        by_key.setdefault(val["event_key"], title)

    for item in new_items:
        action = item.get("event_action")
        if action == "none":
            continue
        event = item["event"]
        title, key = event["title"], event["event_key"]
        known = by_title.get(title)
        other_title = by_key.get(key)
        if known is not None and known != key:
            raise PreflightError("event title has a different published event_key")
        if other_title is not None and other_title != title:
            # Older history may include distinct title aliases for one stable
            # event key. Continue to allow explicit updates of such aliases.
            if action == "create":
                raise PreflightError("event key already belongs to another event")
        if action == "create" and known is not None:
            raise PreflightError("published event must be updated, not recreated")
        if action == "update" and known is None and other_title is None:
            raise PreflightError("unrecognized event cannot be updated")
        by_title.setdefault(title, key)
        by_key.setdefault(key, title)


def prepare(
    incoming: dict, day: str, previous: dict | None,
    history: list[dict], registry: dict,
) -> tuple[dict, str]:
    if not re.fullmatch(r"\d{8}", day):
        raise PreflightError("day must be YYYYMMDD")
    checker.validate_payload(incoming)
    if incoming["batch_id"] != f"{day}-0715":
        raise PreflightError("only a formally approved batch ID may be published")
    if incoming["generated_at_bjt"][:10] != f"{day[:4]}-{day[4:6]}-{day[6:]}":
        raise PreflightError("batch generation date differs from the publish day")
    if any(not item["public_id"].startswith(f"gai-{day}-") for item in incoming["items"]):
        raise PreflightError("article public_id does not match publication day")

    if previous is not None:
        checker.validate_payload(previous)
        if previous["batch_id"] != incoming["batch_id"]:
            raise PreflightError("published batch identity conflict")
        # Source-day identity is maintained even during same-day supplements.
        try:
            result, summary = merger.merge(
                previous, incoming, day, BATCH_ROOT,
                BATCH_ROOT / day / "public-batch.json"
            )
        except (ValueError, KeyError, TypeError) as exc:
            raise PreflightError(str(exc)) from exc
        new_items = result["items"][len(previous["items"]):]
        if summary["skipped_historical"]:
            raise PreflightError("candidate duplicates an older published URL")
        status = "APPEND_READY" if new_items else "ALREADY_SYNCED"
    else:
        result = incoming
        new_items = incoming["items"]
        status = "CREATE_READY"

    historical_ids, historical_urls = history_indexes(history)
    existing_ids, existing_urls = history_indexes([previous] if previous else [])
    for item in new_items:
        if item["public_id"] in historical_ids or item["public_id"] in existing_ids:
            raise PreflightError("duplicate public_id across published history")
        url = normalize_url(item["source_url"])
        if url in historical_urls or url in existing_urls:
            raise PreflightError("duplicate source URL across published history")
        historical_ids.add(item["public_id"])
        historical_urls.add(url)

    verify_event_identity(new_items, registry)
    checker.validate_payload(result)
    return result, status


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--incoming", type=Path, required=True,
                   help="Already-approved candidate JSON outside public Git history")
    p.add_argument("--day", required=True)
    p.add_argument("--output", type=Path, required=True,
                   help="Prepared JSON outside public Git history until QA passes")
    args = p.parse_args()
    if args.incoming.resolve().is_relative_to(ROOT) or args.output.resolve().is_relative_to(ROOT):
        raise SystemExit("incoming/output must be outside the public Git repository")
    incoming = json.loads(args.incoming.read_text(encoding="utf-8"))
    dest = BATCH_ROOT / args.day / "public-batch.json"
    previous = json.loads(dest.read_text(encoding="utf-8")) if dest.exists() else None
    history = [
        json.loads(f.read_text(encoding="utf-8"))
        for f in sorted(BATCH_ROOT.glob("*/public-batch.json"))
        if f != dest
    ]
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    try:
        result, status = prepare(incoming, args.day, previous, history, registry)
    except (PreflightError, checker.ValidationError, ValueError, KeyError, TypeError) as exc:
        print("PREPUBLICATION_REJECTED: " + str(exc))
        return 1
    # The caller must complete manual/LLM confidentiality and source-QA
    # checks before using the prepared JSON in the public GitHub API.
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "batch_id": result["batch_id"],
                      "total_items": len(result["items"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
