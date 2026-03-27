from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from .raw_source.fetch import fetch_source_html


def load_json(path: Union[str, Path]) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_text(path: Union[str, Path]) -> str:
    return Path(path).read_text(encoding="utf-8")


def resolve_raw_html(
    raw_path: Optional[Union[str, Path]],
    source_url: Optional[str],
    metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Optional[str]]:
    if raw_path:
        return load_text(raw_path), str(raw_path)
    candidate_url = source_url or (metadata or {}).get("source_url")
    if not candidate_url:
        raise ValueError("Either raw HTML or a source_url must be provided.")
    return fetch_source_html(candidate_url), candidate_url


def resolve_hint_json(
    rule_json: Dict[str, Any],
    raw_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Auto-resolve and load the hint JSON for a rule.

    Tries two strategies:
    1. If raw_path is given, look for raw/hints/CGST-R{number}.json relative
       to the raw HTML file's grandparent directory.
    2. Fall back to searching relative to raw_path's parent/parent.

    Returns an empty dict if not found (graceful degradation).
    """
    rule_number = (rule_json.get("metadata") or {}).get("rule_number")
    if not rule_number:
        node = rule_json.get("node") or {}
        rule_number = node.get("label")
    if not rule_number:
        return {}

    hint_filename = f"CGST-R{rule_number}.json"

    if raw_path:
        raw_p = Path(raw_path)
        # raw_path is typically .../raw/html/CGST-R8.html
        # hints are at .../raw/hints/CGST-R8.json
        hint_candidate = raw_p.parent.parent / "hints" / hint_filename
        if hint_candidate.exists():
            return load_json(hint_candidate)
        # Also try: sibling 'hints' dir if raw_path is the html dir itself
        hint_candidate = raw_p.parent / "hints" / hint_filename
        if hint_candidate.exists():
            return load_json(hint_candidate)

    return {}
