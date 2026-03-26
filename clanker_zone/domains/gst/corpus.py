from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class GSTRuleBundle(BaseModel):
    corpus_root: str
    schema_path: str
    rule_path: str
    raw_html_path: Optional[str] = None
    hint_path: Optional[str] = None
    section_content_path: Optional[str] = None
    rule_json: Dict[str, Any]
    rule_schema_json: Dict[str, Any]
    raw_html: Optional[str] = None
    hint_json: Dict[str, Any] = {}
    section_content_json: Dict[str, Any] = {}


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_rule_bundle(corpus_root: Path, rule_path: Path) -> GSTRuleBundle:
    rule_json = _load_json(rule_path)
    schema_path = corpus_root / "rule_document.json"
    schema_json = _load_json(schema_path)
    rule_number = rule_json["metadata"]["rule_number"]
    raw_html_path = corpus_root / "raw" / "html" / f"CGST-R{rule_number}.html"
    hint_path = corpus_root / "raw" / "hints" / f"CGST-R{rule_number}.json"
    section_content_path = corpus_root / "section_content.json"
    return GSTRuleBundle(
        corpus_root=str(corpus_root),
        schema_path=str(schema_path),
        rule_path=str(rule_path),
        raw_html_path=str(raw_html_path) if raw_html_path.exists() else None,
        hint_path=str(hint_path) if hint_path.exists() else None,
        section_content_path=str(section_content_path) if section_content_path.exists() else None,
        rule_json=rule_json,
        rule_schema_json=schema_json,
        raw_html=raw_html_path.read_text(encoding="utf-8") if raw_html_path.exists() else None,
        hint_json=_load_json(hint_path) if hint_path.exists() else {},
        section_content_json=_load_json(section_content_path) if section_content_path.exists() else {},
    )


def discover_rule_bundles(corpus_root: Path) -> List[GSTRuleBundle]:
    bundles: List[GSTRuleBundle] = []
    for rule_path in sorted(corpus_root.glob("rule_*.json")):
        if rule_path.name == "rule_document.json":
            continue
        bundles.append(load_rule_bundle(corpus_root, rule_path))
    return bundles
