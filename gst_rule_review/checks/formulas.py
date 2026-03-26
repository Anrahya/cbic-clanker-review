from __future__ import annotations

from .common import build_finding, node_text, source_text
from ..models import CheckContext, CheckResult
from ..raw_source.locators import normalize_text


def run(context: CheckContext) -> CheckResult:
    result = CheckResult()
    for node in context.indexed_rule.nodes.values():
        if node.node_type.lower() != "formula":
            continue
        source_raw = source_text(context, node)
        if source_raw and normalize_text(node_text(node)) != normalize_text(source_raw):
            result.findings.append(
                build_finding(
                    issue_id=f"FORMULA-{node.node_id}",
                    category="formulas",
                    severity="critical",
                    title="Formula text differs from mapped source",
                    problem="The extracted formula does not exactly match the mapped source expression.",
                    node=node,
                    raw_source_fragment=source_raw,
                    why_real_defect="Formula operators, grouping, and variable positions are legally meaningful and should not be normalized loosely.",
                    recommended_fix="Re-extract the formula exactly, preserving operators, brackets, and sequence from the source.",
                    confidence=0.95,
                )
            )
    return result

