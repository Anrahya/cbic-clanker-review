from __future__ import annotations

from .common import build_finding, node_text, source_text
from ..models import CheckContext, CheckResult


ALLOWED_PARENTS = {
    "proviso": {"sub_rule", "rule", "clause"},
    "explanation": {"rule", "sub_rule", "clause"},
}


def run(context: CheckContext) -> CheckResult:
    result = CheckResult()
    for node in context.indexed_rule.nodes.values():
        node_type = node.node_type.lower()
        if node_type not in ALLOWED_PARENTS:
            continue
        parent_id = node.parent_id
        if not parent_id:
            continue
        parent = context.indexed_rule.nodes.get(parent_id)
        if parent and parent.node_type.lower() not in ALLOWED_PARENTS[node_type]:
            result.findings.append(
                build_finding(
                    issue_id=f"SCOPE-{node.node_id}",
                    category="provisos_explanations",
                    severity="major",
                    title=f"{node_type.title()} attached to an implausible parent type",
                    problem=f"The {node_type} is attached to a {parent.node_type} node rather than a rule or sub-rule container.",
                    node=node,
                    raw_source_fragment=source_text(context, node),
                    why_real_defect="Attachment controls legal scope. Attaching a proviso or explanation too low or too high changes which text it qualifies.",
                    recommended_fix=f"Attach the {node_type} to the source unit it actually qualifies, preserving the source hierarchy.",
                    confidence=0.86,
                )
            )
        if node_type == "proviso" and node_text(parent).lower().startswith("provided that"):
            result.findings.append(
                build_finding(
                    issue_id=f"SCOPE-EMBED-{parent.node_id}",
                    category="provisos_explanations",
                    severity="major",
                    title="Proviso text remains embedded in parent body",
                    problem="The parent text itself begins with proviso language while a separate proviso node also exists or should exist.",
                    node=parent,
                    raw_source_fragment=source_text(context, parent),
                    why_real_defect="Treating proviso language as body text blurs scope and prevents precise targeting.",
                    recommended_fix="Split the proviso into its own child node and keep the parent body free of proviso text.",
                    confidence=0.84,
                )
            )
    return result

