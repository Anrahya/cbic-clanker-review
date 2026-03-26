from __future__ import annotations

from .common import build_finding, source_text
from ..models import CheckContext, CheckResult
from ..raw_source.locators import extract_dates, extract_markers


def run(context: CheckContext) -> CheckResult:
    result = CheckResult()
    for node in context.indexed_rule.nodes.values():
        source_raw = source_text(context, node)
        source_markers = set(extract_markers(source_raw))
        node_markers = set(node.amendment_markers)
        if source_markers and node_markers and not node_markers.issubset(source_markers):
            result.findings.append(
                build_finding(
                    issue_id=f"MARKER-SPAN-{node.node_id}",
                    category="amendment_markers",
                    severity="major",
                    title="Marker attached more broadly than the mapped source span",
                    problem="The node carries a marker not present in its mapped source blocks.",
                    node=node,
                    raw_source_fragment=source_raw,
                    why_real_defect="Attaching a marker to the wrong structural level changes which text the amendment is said to affect.",
                    recommended_fix="Move the marker to the child node or narrower span that actually contains the bracketed source text.",
                    confidence=0.94,
                )
            )
        for marker in node_markers:
            source_events = context.raw_source.marker_events.get(marker, [])
            extracted = context.indexed_rule.amendment_map.get(marker)
            if not source_events or not extracted:
                continue
            source_actions = {event.action for event in source_events}
            extracted_action = str(extracted.get("action") or "").upper()
            if extracted_action and extracted_action not in source_actions:
                result.findings.append(
                    build_finding(
                        issue_id=f"MARKER-ACTION-{node.node_id}-{marker}",
                        category="amendment_markers",
                        severity="major",
                        title="Amendment action does not match source footnote",
                        problem=f"The extracted amendment action is {extracted_action}, but the source footnote indicates {', '.join(sorted(source_actions))}.",
                        node=node,
                        raw_source_fragment=" ".join(event.text_fragment for event in source_events),
                        why_real_defect="Amendment action classification is a legal-status field and should follow the source footnote, not a generic notification label.",
                        recommended_fix="Classify the amendment using the explicit action words from the source footnote and preserve auxiliary enforcement metadata separately.",
                        confidence=0.97,
                    )
                )
            if len(source_events) > 1:
                extracted_events = extracted.get("events") or [extracted]
                if len(extracted_events) < len(source_events):
                    result.findings.append(
                        build_finding(
                            issue_id=f"MARKER-COMPOUND-{node.node_id}-{marker}",
                            category="amendment_markers",
                            severity="major",
                            title="Compound footnote lost one or more structured events",
                            problem="The source footnote contains multiple distinct amendment/effective-date events, but the extracted amendments array keeps fewer events.",
                            node=node,
                            raw_source_fragment=" ".join(event.text_fragment for event in source_events),
                            why_real_defect="Compound footnotes carry separate legal facts such as insertion and later enforcement. Merging them loses chronology.",
                            recommended_fix="Emit one structured event per source event fragment and keep notification metadata on each event.",
                            confidence=0.95,
                        )
                    )
            notification_dates = [event.notification_date for event in source_events if event.notification_date]
            if notification_dates and not extracted.get("notification_date"):
                result.findings.append(
                    build_finding(
                        issue_id=f"MARKER-DATE-{node.node_id}-{marker}",
                        category="amendment_markers",
                        severity="moderate",
                        title="Notification date is extractable from footnote but missing from amendment entry",
                        problem="The source footnote contains a notification date that was not captured structurally.",
                        node=node,
                        raw_source_fragment=" ".join(event.text_fragment for event in source_events),
                        why_real_defect="Missing notification dates weakens chronology and provenance even when the footnote otherwise maps correctly.",
                        recommended_fix="Populate notification_date from the amendment footnote text for the relevant event.",
                        confidence=0.89,
                    )
                )
            for event in extracted.get("events", []):
                fragment = str(event.get("event_text") or "")
                if fragment and extract_dates(fragment) and len(fragment.split()) < 4:
                    result.findings.append(
                        build_finding(
                            issue_id=f"MARKER-FRAGMENT-{node.node_id}-{marker}",
                            category="amendment_markers",
                            severity="moderate",
                            title="Amendment event text fragment appears malformed",
                            problem="The stored event_text is too short to represent the source footnote fragment faithfully.",
                            node=node,
                            raw_source_fragment=" ".join(evt.text_fragment for evt in source_events),
                            why_real_defect="Malformed event fragments are usually truncation bugs and are not source-faithful evidence.",
                            recommended_fix="Store the full source fragment for each amendment event.",
                            confidence=0.82,
                        )
                    )
                historical_text = str(event.get("historical_text") or "")
                if historical_text:
                    tail = historical_text.strip().split()[-1]
                    if len(historical_text.split()) >= 4 and len(tail) <= 2 and tail.isalpha():
                        result.findings.append(
                            build_finding(
                                issue_id=f"MARKER-HISTORY-{node.node_id}-{marker}",
                                category="amendment_markers",
                                severity="moderate",
                                title="Historical text appears truncated",
                                problem="The stored historical_text ends mid-token and does not preserve the prior text faithfully.",
                                node=node,
                                raw_source_fragment=" ".join(evt.text_fragment for evt in source_events),
                                why_real_defect="Truncated historical_text is not a stylistic issue; it breaks the audit trail for the prior version of the provision.",
                                recommended_fix="Store the full historical text fragment or omit the field until the reviewer can recover the complete source-backed text.",
                                confidence=0.84,
                            )
                        )
    return result
