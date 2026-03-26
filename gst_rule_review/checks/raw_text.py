from __future__ import annotations

from .common import build_finding, source_text
from ..models import CheckContext, CheckResult
from ..raw_source.locators import extract_markers, normalize_text


def run(context: CheckContext) -> CheckResult:
    result = CheckResult()
    for node in context.indexed_rule.nodes.values():
        if not node.raw_text:
            continue
        source_raw = source_text(context, node)
        if not source_raw:
            continue
        source_markers = set(extract_markers(source_raw))
        node_markers = set(extract_markers(node.raw_text))
        if node.amendment_markers and not node_markers.intersection(set(node.amendment_markers)):
            result.findings.append(
                build_finding(
                    issue_id=f"RAW-{node.node_id}",
                    category="raw_text",
                    severity="major",
                    title="Node raw_text does not preserve mapped amendment marker",
                    problem="The node carries an amendment marker structurally, but the raw_text field does not preserve it.",
                    node=node,
                    raw_source_fragment=source_raw,
                    why_real_defect="raw_text is the provenance field. Dropping the visible marker breaks traceability back to the source span.",
                    recommended_fix="Populate raw_text with the source-faithful marked span, including the relevant bracket marker.",
                    confidence=0.93,
                )
            )
        if source_markers and not node_markers and node.raw_text and normalize_text(node.raw_text) != normalize_text(source_raw):
            result.findings.append(
                build_finding(
                    issue_id=f"RAW-SPAN-{node.node_id}",
                    category="raw_text",
                    severity="moderate",
                    title="Mapped source contains bracket traceability missing from raw_text",
                    problem="The mapped source span contains amendment brackets that are absent from the stored raw_text.",
                    node=node,
                    raw_source_fragment=source_raw,
                    why_real_defect="Bracket traceability is part of the legal provenance trail and should not disappear from raw_text when the source span includes it.",
                    recommended_fix="Rebuild raw_text from the source span and preserve the visible bracket markers.",
                    confidence=0.81,
                )
            )
    return result

