from __future__ import annotations

from .common import build_finding, node_text, source_text
from ..models import CheckContext, CheckResult


CLAUSE_TYPES = {"clause", "sub_clause", "item"}


def run(context: CheckContext) -> CheckResult:
    result = CheckResult()
    for node in context.indexed_rule.nodes.values():
        if node.node_type.lower() not in CLAUSE_TYPES:
            continue
        if node.status == "omitted" and node.text and node.label and node.text.strip() == node.label.strip():
            result.findings.append(
                build_finding(
                    issue_id=f"CLAUSE-{node.node_id}",
                    category="clauses",
                    severity="major",
                    title="Omitted clause text is only the label",
                    problem="The clause body has been replaced with the label token instead of preserving null/empty text for the omitted content.",
                    node=node,
                    raw_source_fragment=source_text(context, node),
                    why_real_defect="Using the label as text invents operative content that never appears in the source.",
                    recommended_fix="Set omitted clause text to null or a schema-permitted empty value and preserve omission through status/amendment fields instead.",
                    confidence=0.97,
                )
            )
        if node.text and node.label and node.text.strip().startswith(node.label.strip() + " "):
            result.findings.append(
                build_finding(
                    issue_id=f"CLAUSE-LABEL-{node.node_id}",
                    category="clauses",
                    severity="minor",
                    title="Clause label appears duplicated inside clause text",
                    problem="The label token appears to have been mixed into the clause body text.",
                    node=node,
                    raw_source_fragment=source_text(context, node),
                    why_real_defect="Label/content mixing can distort exact text comparisons and downstream rendering.",
                    recommended_fix="Keep the label in the structural field and remove it from the clause body when it is not part of the source span.",
                    confidence=0.76,
                )
            )
    return result

