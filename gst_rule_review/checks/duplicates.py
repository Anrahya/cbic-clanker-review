from __future__ import annotations

from .common import build_finding, node_text
from ..models import CheckContext, CheckResult


def run(context: CheckContext) -> CheckResult:
    result = CheckResult()
    for node_id, child_ids in context.indexed_rule.children_map.items():
        parent = context.indexed_rule.nodes.get(node_id)
        if not parent:
            continue
        parent_text = node_text(parent)
        if not parent_text:
            continue
        for child_id in child_ids:
            child = context.indexed_rule.nodes.get(child_id)
            if child and parent_text == node_text(child):
                result.findings.append(
                    build_finding(
                        issue_id=f"DUP-TEXT-{parent.node_id}",
                        category="duplicates",
                        severity="moderate",
                        title="Same text is represented at parent and child node",
                        problem="The parent and child carry identical operative text.",
                        node=parent,
                        raw_source_fragment=parent_text,
                        why_real_defect="Duplicated structural text usually signals a parser duplication bug and can double-count legal content.",
                        recommended_fix="Keep the text only on the node whose source span actually carries it.",
                        confidence=0.88,
                    )
                )
                break
    return result

