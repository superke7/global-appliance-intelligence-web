#!/usr/bin/env python3
"""Validate the standardized public payload using the repository contract."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "config" / "public-batch-contract.json"

TOP_LEVEL_FIELDS = {"schema_version", "batch_id", "generated_at_bjt", "target_publish_at_bjt", "items"}
ITEM_FIELDS = {"public_id", "title", "excerpt", "content_html", "source_name", "source_url", "source_published_date", "event_action", "event"}
EVENT_FIELDS = {"event_key", "title", "date", "latest_progress", "status", "countries", "entities", "category"}
FORBIDDEN_KEYS = {"internal_analysis", "internal_strategy", "internal_risk_level", "internal_priority", "internal_owner", "internal_project", "internal_note", "private_note"}
FORBIDDEN_PHRASES = {"仅供内部", "内部机密", "内部风险等级", "内部负责人", "内部项目编号", "internal use only", "strictly confidential"}

class ValidationError(ValueError):
    """Raised when a payload violates the public contract."""


def load_contract() -> dict[str, Any]:
    try:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot load public contract: {exc}") from exc
    required = {"schema_version", "event_actions", "event_statuses", "event_categories", "event_key_pattern", "legacy_event_update_key_pattern", "public_id_pattern", "batch_id_pattern", "bjt_timestamp_pattern", "date_pattern", "max_items"}
    missing = required - set(contract)
    if missing:
        raise ValidationError(f"public contract missing field(s): {', '.join(sorted(missing))}")
    return contract


CONTRACT = load_contract()
EVENT_ACTIONS = set(CONTRACT["event_actions"])
EVENT_STATUSES = set(CONTRACT["event_statuses"])
EVENT_CATEGORIES = set(CONTRACT["event_categories"])
EVENT_CREATE_KEY_RE = re.compile(CONTRACT["event_key_pattern"])
EVENT_UPDATE_KEY_RE = re.compile(CONTRACT["legacy_event_update_key_pattern"])
PUBLIC_ID_RE = re.compile(CONTRACT["public_id_pattern"])
BATCH_ID_RE = re.compile(CONTRACT["batch_id_pattern"])
BJT_TIMESTAMP_RE = re.compile(CONTRACT["bjt_timestamp_pattern"])
DATE_RE = re.compile(CONTRACT["date_pattern"])
MAX_ITEMS = int(CONTRACT["max_items"])


def fail(path: str, message: str) -> None:
    raise ValidationError(f"{path}: {message}")


def require_nonempty_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(path, "must be a non-empty string")
    return value


def reject_unknown_fields(data: dict[str, Any], allowed: set[str], path: str) -> None:
    unknown = set(data) - allowed
    if unknown:
        fail(path, f"unknown field(s): {', '.join(sorted(unknown))}")


def scan_forbidden_content(value: Any, path: str = "payload") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS:
                fail(f"{path}.{key}", "forbidden internal field")
            scan_forbidden_content(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_forbidden_content(child, f"{path}[{index}]")
    elif isinstance(value, str):
        for phrase in FORBIDDEN_PHRASES:
            if phrase in value:
                fail(path, f"contains forbidden internal phrase: {phrase}")


def validate_date(value: Any, path: str) -> None:
    text = require_nonempty_string(value, path)
    if not DATE_RE.fullmatch(text):
        fail(path, "must satisfy contract date_pattern")


def validate_https_url(value: Any, path: str) -> None:
    text = require_nonempty_string(value, path)
    if any(character.isspace() or ord(character) < 32 for character in text):
        fail(path, "must be a complete HTTPS URL without whitespace")
    try:
        parsed = urlsplit(text)
        port = parsed.port
    except ValueError as exc:
        fail(path, f"invalid HTTPS URL: {exc}")
    if parsed.scheme.lower() != "https" or not parsed.netloc or not parsed.hostname:
        fail(path, "must be a complete HTTPS URL")
    if parsed.username is not None or parsed.password is not None:
        fail(path, "must not contain embedded credentials")
    if port is not None and not 1 <= port <= 65535:
        fail(path, "contains an invalid port")


def validate_string_array(value: Any, path: str) -> None:
    if not isinstance(value, list) or not value:
        fail(path, "must be a non-empty array")
    if len(value) > 20:
        fail(path, "must contain no more than 20 entries")
    for index, entry in enumerate(value):
        require_nonempty_string(entry, f"{path}[{index}]")


def validate_event(event: Any, action: str, path: str) -> None:
    if not isinstance(event, dict):
        fail(path, "must be an object")
    reject_unknown_fields(event, EVENT_FIELDS, path)
    missing = EVENT_FIELDS - set(event)
    if missing:
        fail(path, f"missing field(s): {', '.join(sorted(missing))}")
    event_key = require_nonempty_string(event["event_key"], f"{path}.event_key")
    if action == "create":
        if not EVENT_CREATE_KEY_RE.fullmatch(event_key):
            fail(f"{path}.event_key", "new events must satisfy contract event_key_pattern")
    elif action == "update":
        if not EVENT_UPDATE_KEY_RE.fullmatch(event_key):
            fail(f"{path}.event_key", "event updates must satisfy contract legacy_event_update_key_pattern")
    require_nonempty_string(event["title"], f"{path}.title")
    validate_date(event["date"], f"{path}.date")
    require_nonempty_string(event["latest_progress"], f"{path}.latest_progress")
    if event["status"] not in EVENT_STATUSES:
        fail(f"{path}.status", "unsupported event status")
    validate_string_array(event["countries"], f"{path}.countries")
    validate_string_array(event["entities"], f"{path}.entities")
    if event["category"] not in EVENT_CATEGORIES:
        fail(f"{path}.category", "unsupported event category")


def validate_item(item: Any, index: int, public_ids: set[str]) -> None:
    path = f"payload.items[{index}]"
    if not isinstance(item, dict):
        fail(path, "must be an object")
    reject_unknown_fields(item, ITEM_FIELDS, path)
    required = ITEM_FIELDS - {"event"}
    missing = required - set(item)
    if missing:
        fail(path, f"missing field(s): {', '.join(sorted(missing))}")
    public_id = require_nonempty_string(item["public_id"], f"{path}.public_id")
    if not PUBLIC_ID_RE.fullmatch(public_id):
        fail(f"{path}.public_id", "must satisfy contract public_id_pattern")
    if public_id in public_ids:
        fail(f"{path}.public_id", "duplicate public_id in batch")
    public_ids.add(public_id)
    require_nonempty_string(item["title"], f"{path}.title")
    require_nonempty_string(item["excerpt"], f"{path}.excerpt")
    require_nonempty_string(item["content_html"], f"{path}.content_html")
    require_nonempty_string(item["source_name"], f"{path}.source_name")
    validate_https_url(item["source_url"], f"{path}.source_url")
    validate_date(item["source_published_date"], f"{path}.source_published_date")
    action = item["event_action"]
    if action not in EVENT_ACTIONS:
        fail(f"{path}.event_action", "unsupported event action")
    has_event = "event" in item
    if action == "none" and has_event:
        fail(f"{path}.event", "must be omitted when event_action is none")
    if action in {"create", "update"}:
        if not has_event:
            fail(f"{path}.event", "is required for create or update")
        validate_event(item["event"], action, f"{path}.event")


def validate_payload(payload: Any) -> None:
    if not isinstance(payload, dict):
        fail("payload", "must be an object")
    scan_forbidden_content(payload)
    reject_unknown_fields(payload, TOP_LEVEL_FIELDS, "payload")
    missing = TOP_LEVEL_FIELDS - set(payload)
    if missing:
        fail("payload", f"missing field(s): {', '.join(sorted(missing))}")
    if payload["schema_version"] != CONTRACT["schema_version"]:
        fail("payload.schema_version", "unsupported schema version")
    batch_id = require_nonempty_string(payload["batch_id"], "payload.batch_id")
    if not BATCH_ID_RE.fullmatch(batch_id):
        fail("payload.batch_id", "must satisfy contract batch_id_pattern")
    for field in ("generated_at_bjt", "target_publish_at_bjt"):
        timestamp = require_nonempty_string(payload[field], f"payload.{field}")
        if not BJT_TIMESTAMP_RE.fullmatch(timestamp):
            fail(f"payload.{field}", "must satisfy contract bjt_timestamp_pattern")
    items = payload["items"]
    if not isinstance(items, list):
        fail("payload.items", "must be an array")
    if len(items) > MAX_ITEMS:
        fail("payload.items", f"must contain no more than {MAX_ITEMS} entries")
    public_ids: set[str] = set()
    for index, item in enumerate(items):
        validate_item(item, index, public_ids)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate-public-payload.py <payload.json>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        validate_payload(payload)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"Public payload validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"Public payload validation OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
