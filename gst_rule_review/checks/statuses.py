from __future__ import annotations

from .common import build_finding, source_text
from ..models import CheckContext, CheckResult


def run(context: CheckContext) -> CheckResult:
    result = CheckResult()
    for node in context.indexed_rule.nodes.values():
        status = (node.status or "").lower()
        if not status:
            continue
        marker_actions = set()
        for marker in node.amendment_markers:
            marker_actions.update(event.action.lower() for event in context.raw_source.marker_events.get(marker, []))
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
    return result

