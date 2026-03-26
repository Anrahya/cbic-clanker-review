from __future__ import annotations

from typing import Dict, List, Optional

from ...models import CandidateIssue, Dossier, RuleSynthesisReport


def apply_gst_false_positive_filter(
    *,
    report: RuleSynthesisReport,
    dossiers: List[Dossier],
) -> RuleSynthesisReport:
    dossier_map: Dict[str, Dossier] = {dossier.dossier_id: dossier for dossier in dossiers}
    node_map: Dict[str, Dossier] = {}
    for dossier in dossiers:
        node_map.setdefault(dossier.target_id, dossier)
        for node_id in dossier.metadata.get("target_node_ids", []):
            node_map.setdefault(node_id, dossier)
    confirmed: List[CandidateIssue] = []
    accepted = list(report.accepted_artifacts)
    manual = list(report.manual_review_issues)
    rejected = list(report.rejected_issues)

    for issue in report.confirmed_issues:
        dossier = dossier_map.get(issue.dossier_id) or node_map.get(issue.node_id or "")
        if issue.node_id and issue.node_id in node_map:
            dossier = node_map[issue.node_id]
        disposition = _classify_issue(issue, dossier)
        if disposition == "acceptable_artifact":
            accepted.append(issue)
        elif disposition == "needs_manual_review":
            manual.append(issue)
        else:
            confirmed.append(issue)

    if confirmed:
        status = "issues_found"
        summary = f"{len(confirmed)} confirmed issue(s) remain after challenge, arbitration, and GST false-positive filtering."
    elif manual:
        status = "needs_manual_review"
        summary = f"No issue survived GST false-positive filtering, but {len(manual)} item(s) still need manual review."
    else:
        status = "clean"
        summary = "No candidate issues survived challenge, arbitration, and GST false-positive filtering."

    return RuleSynthesisReport(
        rule_id=report.rule_id,
        status=status,
        confirmed_issues=confirmed,
        accepted_artifacts=accepted,
        manual_review_issues=manual,
        rejected_issues=rejected,
        summary=summary,
    )


def _classify_issue(issue: CandidateIssue, dossier: Optional[Dossier]) -> Optional[str]:
    text = " ".join(part for part in [issue.title, issue.problem, issue.category] if part).lower()
    target_summary = _target_summary(dossier, issue.node_id)
    candidate = target_summary or (dossier.candidate_fragment if dossier is not None else {})
    carry_in_span = _has_carry_in_amendment_span(dossier, issue.node_id)

    if "target_id" in text and "external_act" in text:
        return "acceptable_artifact"

    if "anchor_text" in text:
        return "acceptable_artifact"

    if "bracket" in text and carry_in_span:
        return "acceptable_artifact"

    if "leading enumeration label" in text or "display_label" in text or "clause label prefix" in text:
        if candidate.get("display_label"):
            return "acceptable_artifact"

    if issue.category == "redundant_chronology" or "effective_until duplicates status=omitted" in text:
        return "acceptable_artifact"

    if "duplicate" in text and "sibling" in text and issue.category == "cross_refs":
        return "acceptable_artifact"

    if "amendment marker" in text and carry_in_span:
        return "acceptable_artifact"

    if "missing effective_from" in text:
        return "needs_manual_review"

    return None


def _has_carry_in_amendment_span(dossier: Optional[Dossier], node_id: Optional[str]) -> bool:
    if dossier is None:
        return False
    target_summary = _target_summary(dossier, node_id)
    source_ref = (target_summary or dossier.candidate_fragment).get("source_ref") or {}
    start_block = source_ref.get("start_block")
    if not start_block:
        start_block = _target_start_block(dossier, node_id)
    if not start_block:
        return False
    for snippet in dossier.evidence:
        if snippet.kind != "amendment_span" or not snippet.payload:
            continue
        open_block = snippet.payload.get("open_block")
        close_block = snippet.payload.get("close_block")
        if open_block and close_block and open_block < start_block <= close_block:
            return True
    return False


def _target_summary(dossier: Optional[Dossier], node_id: Optional[str]) -> Optional[dict]:
    if dossier is None:
        return None
    if node_id is None and dossier.kind != "cluster":
        return dossier.candidate_fragment
    if node_id is None:
        node_id = dossier.target_id
    for snippet in dossier.evidence:
        if snippet.kind != "target_card" or not snippet.payload:
            continue
        if snippet.payload.get("id") != node_id:
            continue
        summary = dict(snippet.payload)
        summary["source_ref"] = {
            "start_block": snippet.locator.start,
            "end_block": snippet.locator.end,
        }
        return summary
    return None


def _target_start_block(dossier: Optional[Dossier], node_id: Optional[str]) -> Optional[int]:
    if dossier is None:
        return None
    if node_id is None:
        node_id = dossier.target_id
    for snippet in dossier.evidence:
        if snippet.kind != "target_card" or not snippet.payload:
            continue
        if snippet.payload.get("id") == node_id:
            return snippet.locator.start
    return None
