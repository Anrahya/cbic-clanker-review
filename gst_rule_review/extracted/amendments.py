from __future__ import annotations

from typing import Any


def build_amendment_map(rule_json: dict[str, Any]) -> dict[str, dict[str, Any]]:
    amendment_map: dict[str, dict[str, Any]] = {}
    for entry in rule_json.get("amendments", []):
        marker = str(entry.get("marker") or entry.get("marker_id") or "").strip("[]")
        if marker:
            amendment_map[marker] = entry
    return amendment_map

