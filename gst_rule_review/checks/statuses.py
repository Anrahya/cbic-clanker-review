from __future__ import annotations

import re

from .common import build_finding, source_text
from ..models import CheckContext, CheckResult

_OMISSION_PATTERN = re.compile(r"^\s*\*{2,}\s*$")


def run(context: CheckContext) -> CheckResult:
    result = CheckResult()
    for node in context.indexed_rule.nodes.values():
        status = (node.status or "").lower()
        if not status:
            continue
        marker_actions = set()
        for marker in node.amendment_markers:
            marker_actions.update(event.action.lower() for event in context.raw_source.marker_events.get(marker, []))

        # --- Existing: status=omitted but source doesn't say OMITTED ---
        if status == "omitted" and marker_actions and "omitted" not in marker_actions:
            result.findings.append(
                build_finding(
                    issue_id=f"STATUS-ACTION-{node.node_id}",
                    category="statuses",
                    severity="major",
                    title="Node status is omitted but source footnote does not support omission",
                    problem="The node is marked omitted even though its mapped amendment markers do not indicate omission.",
                    node=node,
                    raw_source_fragment=source_text(context, node),
                    why_real_defect="Status must reflect the source amendment action, not a generic review assumption.",
                    recommended_fix="Align status with the source footnote action or move the marker to the correct node.",
                    confidence=0.9,
                )
            )

        # --- Existing: omitted node effective_from matches omission date ---
        if status == "omitted":
            omission_dates = [
                event.effective_date or event.notification_date
                for marker in node.amendment_markers
                for event in context.raw_source.marker_events.get(marker, [])
                if event.action == "OMITTED"
            ]
            if omission_dates and node.effective_from and node.effective_from in omission_dates:
                result.findings.append(
                    build_finding(
                        issue_id=f"STATUS-DATE-{node.node_id}",
                        category="statuses",
                        severity="major",
                        title="Omitted node effective_from matches omission date",
                        problem="The node version's effective_from was set to the omission date instead of the date when that version came into force.",
                        node=node,
                        raw_source_fragment=source_text(context, node),
                        why_real_defect="The omission date ends a version; it does not usually start the omitted text version.",
                        recommended_fix="Keep effective_from as the version's start date and use effective_until or amendment chronology to record the omission date.",
                        confidence=0.93,
                    )
                )

        # --- NEW: Reverse check — all markers say OMITTED but status != omitted ---
        if status != "omitted" and marker_actions and marker_actions == {"omitted"}:
            result.findings.append(
                build_finding(
                    issue_id=f"STATUS-NOT-OMITTED-{node.node_id}",
                    category="statuses",
                    severity="major",
                    title="All amendment markers indicate omission but node status is not omitted",
                    problem=(
                        f"Every source footnote marker on this node has action 'OMITTED', "
                        f"but the node status is '{status}'."
                    ),
                    node=node,
                    raw_source_fragment=source_text(context, node),
                    why_real_defect=(
                        "If every amendment marker points to an OMITTED action, the node "
                        "should carry status 'omitted'. A mismatch means the provision's "
                        "legal lifecycle is misrepresented."
                    ),
                    recommended_fix="Set the node status to 'omitted' to match the source amendment actions.",
                    confidence=0.91,
                )
            )

        # --- NEW: Omitted text indicator check ---
        if status == "omitted":
            node_text = node.text or ""
            if node_text.strip() and not _OMISSION_PATTERN.match(node_text):
                # Node claims to be omitted but has real text, not just ***
                result.findings.append(
                    build_finding(
                        issue_id=f"STATUS-TEXT-{node.node_id}",
                        category="statuses",
                        severity="moderate",
                        title="Omitted node carries substantive text instead of omission indicator",
                        problem=(
                            "The node has status 'omitted' but its text is substantive content, "
                            "not an omission indicator like '***'."
                        ),
                        node=node,
                        raw_source_fragment=source_text(context, node),
                        why_real_defect=(
                            "When a provision is omitted, the source page typically shows '***' "
                            "or equivalent. Carrying the original text on an omitted node creates "
                            "ambiguity about which version of the text is being represented."
                        ),
                        recommended_fix=(
                            "Either replace the text with the omission indicator from the source, "
                            "or review whether the node should actually be 'active' (with the text "
                            "representing the post-substitution version)."
                        ),
                        confidence=0.82,
                    )
                )

    return result

