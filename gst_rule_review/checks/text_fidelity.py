from __future__ import annotations

from .common import build_finding, node_text, normalized_equal, source_text
from ..models import CheckContext, CheckResult


def run(context: CheckContext) -> CheckResult:
    result = CheckResult()
    for node in context.indexed_rule.nodes.values():
        text = node_text(node)
        if not text:
            continue
        raw = source_text(context, node)
        if not raw:
            continue
        if normalized_equal(text, raw):
            continue
        if context.config.tolerate_cbic_spacing_artifacts and normalized_equal(text, raw):
            continue
        normalized_node = source_text(context, node, normalized=True)
        if normalized_node and normalized_node.startswith(text.strip()) and len(normalized_node) - len(text.strip()) > 20:
            result.findings.append(
                build_finding(
                    issue_id=f"TEXT-{node.node_id}",
                    category="text_fidelity",
                    severity="major",
                    title="Node text appears truncated against mapped source",
                    problem="The extracted operative text stops materially earlier than the mapped source span.",
                    node=node,
                    raw_source_fragment=raw,
                    why_real_defect="The mismatch is substantive rather than cosmetic; the extracted text omits source content within the node's own source span.",
                    recommended_fix="Re-extract the node text from the mapped source blocks without truncating the sentence.",
                    confidence=0.88,
                )
            )
    return result

