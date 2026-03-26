from __future__ import annotations

from .common import build_finding, make_false_positive, node_text, similar, source_blocks
from ..models import CheckContext, CheckResult


def run(context: CheckContext) -> CheckResult:
    result = CheckResult()
    for node_id, node in context.indexed_rule.nodes.items():
        children = [context.indexed_rule.nodes[child_id] for child_id in context.indexed_rule.children_map.get(node_id, [])]
        if not children:
            continue
        text = node_text(node)
        if not text and context.config.allow_textless_structural_nodes:
            result.likely_false_positives.append(
                make_false_positive(
                    title="Textless structural container allowed by config/schema",
                    reason="The node has children and no operative text. The reviewer is configured to treat textless containers as acceptable unless source evidence shows otherwise.",
                    node=node,
                    raw_text="",
                )
            )
        first_child = children[0]
        if text and node_text(first_child) and similar(text, node_text(first_child)) > 0.96:
            result.findings.append(
                build_finding(
                    issue_id=f"STRUCT-{node.node_id}",
                    category="structure",
                    severity="major",
                    title="Parent branch appears collapsed into first child",
                    problem="The parent node text substantially duplicates the first child, which usually indicates the branch container was collapsed into the first descendant.",
                    node=node,
                    raw_source_fragment=text,
                    why_real_defect="This changes structure and scope. A branch node should not consume only the first child when later siblings continue the branch.",
                    recommended_fix="Model the parent as a structural branch and move the duplicated operative text down to the correct child span only.",
                    confidence=0.94,
                )
            )
        source_ref = node.source_ref or {}
        if source_ref.get("exact") and children:
            parent_blocks = set(source_blocks(node))
            child_blocks = set()
            for child in children:
                child_blocks.update(source_blocks(child))
            if parent_blocks and child_blocks and parent_blocks != child_blocks and parent_blocks.issubset(child_blocks):
                result.findings.append(
                    build_finding(
                        issue_id=f"STRUCT-SPAN-{node.node_id}",
                        category="structure",
                        severity="major",
                        title="Container source_ref is too narrow for its children",
                        problem="The node is marked as an exact source span, but its coverage only matches part of the child branch coverage.",
                        node=node,
                        raw_source_fragment="",
                        why_real_defect="An exact source_ref that covers only the first child misstates the source extent of the parent structural node.",
                        recommended_fix="Broaden the parent source_ref to the full branch span or mark it non-exact if it is intentionally structural only.",
                        confidence=0.9,
                    )
                )
    return result

