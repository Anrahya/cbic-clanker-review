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
    rule_metadata: Dict[str, Any] = {}
    raw_html_metadata: Dict[str, Any] = {}
    hint_metadata: Dict[str, Any] = {}

def _compute_file_metadata(path: Optional[Path]) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    import hashlib
    content = path.read_bytes()
    return {
        "mtime": path.stat().st_mtime,
        "sha256": hashlib.sha256(content).hexdigest()
    }


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
        rule_metadata=_compute_file_metadata(rule_path),
        raw_html_metadata=_compute_file_metadata(raw_html_path) if raw_html_path.exists() else {},
        hint_metadata=_compute_file_metadata(hint_path) if hint_path.exists() else {},
    )


def discover_rule_bundles(corpus_root: Path) -> List[GSTRuleBundle]:
    bundles: List[GSTRuleBundle] = []
    for rule_path in sorted(corpus_root.glob("rule_*.json")):
        if rule_path.name == "rule_document.json":
            continue
        bundles.append(load_rule_bundle(corpus_root, rule_path))
    return bundles


def discover_rule_bundles_from_chapters(data_root: Path) -> List[GSTRuleBundle]:
    """Discover rule bundles from a chapter-based directory layout.

    Expected layout:
        data_root/
            chapter_01_xxx/rule_008.json, rule_009.json, ...
            chapter_02_xxx/rule_010.json, ...
            raw/html/CGST-R8.html, ...
            raw/hints/CGST-R8.json, ...
            rule_document.json  (schema)

    The raw/ and schema files live at data_root level, while rule JSONs
    are nested inside chapter_* subdirectories.
    """
    bundles: List[GSTRuleBundle] = []
    for chapter_dir in sorted(data_root.glob("chapter_*")):
        if not chapter_dir.is_dir():
            continue
        for rule_path in sorted(chapter_dir.glob("rule_*.json")):
            if rule_path.name in ("rule_document.json", "chapter_manifest.json"):
                continue
            bundles.append(load_rule_bundle(data_root, rule_path))
    return bundles
