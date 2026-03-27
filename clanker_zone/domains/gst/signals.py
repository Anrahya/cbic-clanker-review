"""Bridge: run deterministic checks and format heuristic signals as neutral dossier evidence."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from ...models import EvidenceLocator, EvidenceSnippet
from gst_rule_review.engine.run_review import review_rule_files
from gst_rule_review.models import Finding


def run_heuristic_signals(
    *,
    rule_path: Path,
    schema_path: Path,
    raw_path: Optional[Path] = None,
    hint_json: Optional[Dict[str, Any]] = None,
) -> List[EvidenceSnippet]:
    """Run deterministic checks, filter to heuristics, and return as neutral evidence snippets."""
    report = review_rule_files(
        rule_path=rule_path,
        schema_path=schema_path,
        raw_path=raw_path,
        hint_json=hint_json or {},
    )
    snippets: List[EvidenceSnippet] = []
    for finding in report.confirmed_issues:
        if finding.signal_class != "heuristic":
            continue
        snippets.append(_finding_to_snippet(finding))
    return snippets


def _finding_to_snippet(finding: Finding) -> EvidenceSnippet:
    """Convert a heuristic Finding into a neutral EvidenceSnippet for dossier injection."""
    return EvidenceSnippet(
        kind="deterministic_signal",
        label=f"{finding.issue_id}",
        locator=EvidenceLocator(
            source_name="deterministic_check",
            pointer=finding.node_id or "",
            start=finding.source_locator.block_ids[0] if finding.source_locator.block_ids else None,
            end=finding.source_locator.block_ids[-1] if finding.source_locator.block_ids else None,
        ),
        # Neutral framing: observation + data, no verdict language
        text=(
            f"[{finding.category}] {finding.title}: {finding.problem}"
        ),
        payload={
            "issue_id": finding.issue_id,
            "node_id": finding.node_id,
            "category": finding.category,
            "severity": finding.severity,
            "signal_class": finding.signal_class,
            "confidence": finding.confidence,
        },
    )


def signals_for_node(
    signals: List[EvidenceSnippet],
    node_id: str,
) -> List[EvidenceSnippet]:
    """Filter signals relevant to a specific node_id."""
    return [
        s for s in signals
        if s.payload and s.payload.get("node_id") == node_id
    ]
