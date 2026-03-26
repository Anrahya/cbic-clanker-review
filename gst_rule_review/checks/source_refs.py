from __future__ import annotations

from .common import build_finding, node_text, source_text
from ..models import CheckContext, CheckResult


REAL_NODE_TYPES = {
    "rule",
    "sub_rule",
    "clause",
    "sub_clause",
    "proviso",
    "explanation",
    "table",
    "formula",
}


def run(context: CheckContext) -> CheckResult:
    result = CheckResult()
    block_ids_in_source = {block.block_id for block in context.raw_source.blocks}
    for node_id, node in context.indexed_rule.nodes.items():
        node_type = node.node_type.lower()
        source_ref = node.source_ref or {}
        block_ids = source_ref.get("block_ids") or source_ref.get("blocks") or []
        if node_type in REAL_NODE_TYPES and not block_ids:
            if not (context.config.allow_textless_structural_nodes and context.indexed_rule.children_map.get(node_id)):
                result.findings.append(
                    build_finding(
                        issue_id=f"SRC-MISSING-{node.node_id}",
                        category="source_refs",
                        severity="moderate",
                        title="Real node is missing source_ref coverage",
                        problem="The node has legal content but no mapped source blocks.",
                        node=node,
                        raw_source_fragment="",
                        why_real_defect="Without source_ref coverage the reviewer cannot audit provenance or cross-check fidelity.",
                        recommended_fix="Map the node to the raw source blocks it was extracted from.",
                        confidence=0.92,
                    )
                )
            continue
        if any(int(block_id) not in block_ids_in_source for block_id in block_ids):
            result.findings.append(
                build_finding(
                    issue_id=f"SRC-BLOCK-{node.node_id}",
                    category="source_refs",
                    severity="moderate",
                    title="source_ref points to a non-existent raw block id",
                    problem="One or more source_ref block ids do not exist in the parsed raw source model.",
                    node=node,
                    raw_source_fragment="",
                    why_real_defect="Broken block ids make the provenance claim unauditable.",
                    recommended_fix="Regenerate source_ref using block ids from the current raw source block map.",
                    confidence=0.94,
                )
            )
        if block_ids and node_text(node):
            raw = source_text(context, node, normalized=True)
            if raw and node_text(node) not in raw and source_ref.get("exact"):
                result.findings.append(
                    build_finding(
                        issue_id=f"SRC-PRECISION-{node.node_id}",
                        category="source_refs",
                        severity="major",
                        title="Exact source_ref does not align with node text",
                        problem="The node is marked as an exact span, but the mapped source blocks do not contain the node text faithfully.",
                        node=node,
                        raw_source_fragment=source_text(context, node),
                        why_real_defect="An exact span claim should only be used when the mapped source blocks actually carry the node's text.",
                        recommended_fix="Correct the block ids or downgrade the source_ref from exact to container coverage where appropriate.",
                        confidence=0.9,
                    )
                )
    return result

