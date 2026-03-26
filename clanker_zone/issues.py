from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional

from .models import CandidateIssue, ExecutedTaskResult, Severity


_SPACE_RE = re.compile(r"\s+")
_NON_WORD_RE = re.compile(r"[^a-z0-9]+")
_SEVERITY_RANK: Dict[Optional[Severity], int] = {
    None: 0,
    "minor": 1,
    "moderate": 2,
    "major": 3,
    "critical": 4,
}


def aggregate_candidate_issues(results: Iterable[ExecutedTaskResult]) -> List[CandidateIssue]:
    grouped: Dict[str, CandidateIssue] = {}
    for result in results:
        judgment = result.parsed_judgment
        if judgment is None or judgment.label != "confirmed_issue":
            continue
        signature = issue_signature(result)
        issue = grouped.get(signature)
        if issue is None:
            issue = CandidateIssue(
                issue_id=f"ISSUE-{len(grouped) + 1:04d}",
                signature=signature,
                dossier_id=result.dossier_id,
                node_id=judgment.node_id,
                category=judgment.category,
                severity=judgment.severity,
                title=judgment.title,
                problem=judgment.problem,
                evidence_refs=list(dict.fromkeys(judgment.evidence_refs)),
                recommended_fix=judgment.recommended_fix,
                supporting_task_ids=[result.task_id],
                supporting_counsel=[result.counsel_name],
                metadata={
                    "judgment_labels": [judgment.label],
                    "max_confidence": judgment.confidence,
                },
            )
            grouped[signature] = issue
            continue
        issue.evidence_refs = _merge_unique(issue.evidence_refs, judgment.evidence_refs)
        issue.supporting_task_ids = _merge_unique(issue.supporting_task_ids, [result.task_id])
        issue.supporting_counsel = _merge_unique(issue.supporting_counsel, [result.counsel_name])
        issue.metadata["judgment_labels"] = _merge_unique(issue.metadata.get("judgment_labels", []), [judgment.label])
        issue.metadata["max_confidence"] = max(float(issue.metadata.get("max_confidence", 0.0)), judgment.confidence)
        if _SEVERITY_RANK[judgment.severity] > _SEVERITY_RANK[issue.severity]:
            issue.severity = judgment.severity
        if not issue.title and judgment.title:
            issue.title = judgment.title
        if not issue.problem and judgment.problem:
            issue.problem = judgment.problem
        if not issue.recommended_fix and judgment.recommended_fix:
            issue.recommended_fix = judgment.recommended_fix
        if not issue.node_id and judgment.node_id:
            issue.node_id = judgment.node_id
        if not issue.category and judgment.category:
            issue.category = judgment.category
    return list(grouped.values())


def issue_signature(result: ExecutedTaskResult) -> str:
    judgment = result.parsed_judgment
    if judgment is None:
        raise ValueError("Cannot create issue signature without a parsed judgment.")
    parts = [
        result.dossier_id,
        judgment.node_id or "",
        judgment.category or "",
        _normalize_text(judgment.title or ""),
        _normalize_text(judgment.problem or ""),
    ]
    return "::".join(parts)


def _merge_unique(existing: List[str], incoming: List[str]) -> List[str]:
    seen = dict.fromkeys(existing)
    for item in incoming:
        seen.setdefault(item, None)
    return list(seen.keys())


def _normalize_text(text: str) -> str:
    collapsed = _SPACE_RE.sub(" ", text.strip().lower())
    return _NON_WORD_RE.sub("-", collapsed).strip("-")
