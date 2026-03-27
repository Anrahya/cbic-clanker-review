from __future__ import annotations

from typing import Any, Dict, List, Optional

from .common import build_finding
from ..models import CheckContext, CheckResult


def _build_hint_amendment_index(context: CheckContext) -> Dict[str, Dict[str, Any]]:
    """Build a lookup from marker string → hint amendment entry."""
    amendments: List[Dict[str, Any]] = context.hint_json.get("amendments", [])
    index: Dict[str, Dict[str, Any]] = {}
    for amendment in amendments:
        marker = str(amendment.get("marker", ""))
        if marker:
            index[marker] = amendment
    return index


def run(context: CheckContext) -> CheckResult:
    result = CheckResult()

    # --- Existing check: date inversion ---
    for node in context.indexed_rule.nodes.values():
        if node.effective_from and node.effective_until and node.effective_until < node.effective_from:
            result.findings.append(
                build_finding(
                    issue_id=f"CHRON-{node.node_id}",
                    category="chronology",
                    severity="major",
                    title="Node chronology is internally inconsistent",
                    problem="effective_until is earlier than effective_from.",
                    node=node,
                    raw_source_fragment="",
                    why_real_defect="Internal date inversion breaks lifecycle semantics for the extracted version.",
                    recommended_fix="Correct the node chronology so effective_from is not later than effective_until.",
                    confidence=0.98,
                )
            )

    # --- Tiered effective_date checks (requires hint_json) ---
    if not context.hint_json:
        return result

    hint_index = _build_hint_amendment_index(context)
    if not hint_index:
        return result

    for node in context.indexed_rule.nodes.values():
        if not node.amendment_markers:
            continue

        for marker in node.amendment_markers:
            marker_str = str(marker)
            hint_amendment = hint_index.get(marker_str)
            if not hint_amendment:
                continue

            hint_effective = hint_amendment.get("effective_date")
            hint_enacted = hint_amendment.get("enacted_date") or hint_amendment.get("notification_date")

            if hint_effective:
                # TIER 1 (major): Hint has a clear effective_date
                if node.effective_from and node.effective_from != hint_effective:
                    result.findings.append(
                        build_finding(
                            issue_id=f"CHRON-EFFECTIVE-MISMATCH-{node.node_id}-{marker_str}",
                            category="chronology",
                            severity="major",
                            title="Node effective_from does not match hint effective_date",
                            problem=(
                                f"The hint amendment for marker {marker_str} has effective_date "
                                f"'{hint_effective}', but the node's effective_from is '{node.effective_from}'."
                            ),
                            node=node,
                            raw_source_fragment=hint_amendment.get("text", ""),
                            why_real_defect=(
                                "The w.e.f. date from the source footnote is the authoritative effective date. "
                                "A mismatch means the node's version lifecycle is incorrectly dated."
                            ),
                            recommended_fix="Set the node's effective_from to match the hint amendment's effective_date.",
                            confidence=0.95,
                        )
                    )
                elif not node.effective_from:
                    result.findings.append(
                        build_finding(
                            issue_id=f"CHRON-EFFECTIVE-MISSING-{node.node_id}-{marker_str}",
                            category="chronology",
                            severity="major",
                            title="Node is missing effective_from despite hint having effective_date",
                            problem=(
                                f"The hint amendment for marker {marker_str} has effective_date "
                                f"'{hint_effective}', but the node has no effective_from."
                            ),
                            node=node,
                            raw_source_fragment=hint_amendment.get("text", ""),
                            why_real_defect=(
                                "A known effective date exists in the source footnote but was not "
                                "propagated to the extracted node, leaving its lifecycle ambiguous."
                            ),
                            recommended_fix=f"Set effective_from to '{hint_effective}' from the amendment footnote.",
                            confidence=0.93,
                        )
                    )
            elif hint_enacted:
                # TIER 2 (moderate): Has enacted_date but no effective_date
                # The source says e.g. "Inserted vide Notification No.X, dated Y"
                # but does not specify "w.e.f." — ambiguous
                if not node.effective_from:
                    result.findings.append(
                        build_finding(
                            issue_id=f"CHRON-DATE-AMBIGUOUS-{node.node_id}-{marker_str}",
                            category="chronology",
                            severity="moderate",
                            title="Amendment has enacted_date but no clear effective date",
                            problem=(
                                f"The hint amendment for marker {marker_str} was enacted on "
                                f"'{hint_enacted}' but the source footnote does not specify a "
                                f"w.e.f. date. The node has no effective_from."
                            ),
                            node=node,
                            raw_source_fragment=hint_amendment.get("text", ""),
                            why_real_defect=(
                                "When a notification does not specify 'w.e.f.', the effective date "
                                "may default to the notification date or to a separately notified "
                                "enforcement date. This ambiguity requires manual legal review."
                            ),
                            recommended_fix=(
                                "Verify whether the amendment took effect on the enacted date or "
                                "awaits a separate enforcement notification. Set effective_from accordingly."
                            ),
                            confidence=0.72,
                        )
                    )
            else:
                # TIER 3 (minor): No dates at all in the hint
                if not node.effective_from:
                    result.findings.append(
                        build_finding(
                            issue_id=f"CHRON-DATE-MISSING-{node.node_id}-{marker_str}",
                            category="chronology",
                            severity="minor",
                            title="Amendment has no date information in hint or node",
                            problem=(
                                f"The hint amendment for marker {marker_str} has no effective_date "
                                f"or enacted_date, and the node has no effective_from."
                            ),
                            node=node,
                            raw_source_fragment=hint_amendment.get("text", ""),
                            why_real_defect=(
                                "Missing date metadata weakens the audit trail, though this "
                                "may reflect a genuinely undated source footnote."
                            ),
                            recommended_fix="Investigate the original notification to determine the applicable date.",
                            confidence=0.55,
                        )
                    )

    return result

