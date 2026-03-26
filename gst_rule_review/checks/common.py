from __future__ import annotations

from typing import Any, List, Optional

from rapidfuzz.fuzz import ratio

from ..models import CheckContext, Finding, IndexedNode, LikelyFalsePositive, SourceLocator
from ..raw_source.block_map import get_combined_text
from ..raw_source.locators import normalize_text


def node_text(node: IndexedNode) -> str:
    return node.operative_text or node.text or ""


def source_text(context: CheckContext, node: IndexedNode, normalized: bool = False) -> str:
    source_ref = node.source_ref or {}
    block_ids = source_ref.get("block_ids") or source_ref.get("blocks") or []
    return get_combined_text(context.raw_source, [int(block_id) for block_id in block_ids], normalized=normalized)


def build_finding(
    issue_id: str,
    category: str,
    severity: str,
    title: str,
    problem: str,
    node: Optional[IndexedNode],
    raw_source_fragment: str,
    why_real_defect: str,
    recommended_fix: str,
    confidence: float = 0.85,
) -> Finding:
    locator = SourceLocator()
    json_fragment: Any = None
    if node is not None:
        source_ref = node.source_ref or {}
        locator = SourceLocator(
            block_ids=[int(block_id) for block_id in source_ref.get("block_ids", source_ref.get("blocks", []))],
            line_hint=source_ref.get("line_hint"),
            dom_path=source_ref.get("dom_path"),
        )
        json_fragment = node.node
    return Finding(
        issue_id=issue_id,
        node_id=node.node_id if node else None,
        json_path=node.json_path if node else None,
        category=category,
        severity=severity,  # type: ignore[arg-type]
        title=title,
        problem=problem,
        raw_source_fragment=raw_source_fragment or None,
        source_locator=locator,
        json_fragment=json_fragment,
        why_real_defect=why_real_defect,
        recommended_fix=recommended_fix,
        confidence=confidence,
    )


def similar(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return ratio(normalize_text(a), normalize_text(b)) / 100.0


def normalized_equal(a: str, b: str) -> bool:
    return normalize_text(a) == normalize_text(b)


def source_blocks(node: IndexedNode) -> List[int]:
    source_ref = node.source_ref or {}
    return [int(block_id) for block_id in source_ref.get("block_ids", source_ref.get("blocks", []))]


def make_false_positive(title: str, reason: str, node: Optional[IndexedNode], raw_text: str) -> LikelyFalsePositive:
    return LikelyFalsePositive(
        title=title,
        reason=reason,
        raw_source_fragment=raw_text or None,
        json_fragment=node.node if node else None,
    )
