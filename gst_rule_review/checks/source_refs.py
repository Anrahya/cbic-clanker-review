from __future__ import annotations

from typing import List, Optional

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


def _source_ref_end_block(node) -> Optional[int]:
    """Extract end_block from a node's source_ref."""
    source_ref = node.source_ref or {}
    end = source_ref.get("end_block")
    if end is not None:
        return int(end)
    block_ids = source_ref.get("block_ids") or source_ref.get("blocks") or []
    if block_ids:
        return max(int(b) for b in block_ids)
    return None


def _source_ref_start_block(node) -> Optional[int]:
    """Extract start_block from a node's source_ref."""
    source_ref = node.source_ref or {}
    start = source_ref.get("start_block")
    if start is not None:
        return int(start)
    block_ids = source_ref.get("block_ids") or source_ref.get("blocks") or []
    if block_ids:
        return min(int(b) for b in block_ids)
    return None


def run(context: CheckContext) -> CheckResult:
    result = CheckResult()
    block_ids_in_source = {block.block_id for block in context.raw_source.blocks}

    for node_id, node in context.indexed_rule.nodes.items():
        node_type = node.node_type.lower()
        source_ref = node.source_ref or {}
        block_ids = source_ref.get("block_ids") or source_ref.get("blocks") or []

        # --- Existing: Missing source_ref ---
        if node_type in REAL_NODE_TYPES and not block_ids:
            # Also check start_block/end_block keys (alternative format)
            if not source_ref.get("start_block"):
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

        # --- Existing: Broken block IDs ---
        if block_ids and any(int(block_id) not in block_ids_in_source for block_id in block_ids):
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

        # --- Existing: Exact span doesn't contain node text ---
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

        # --- NEW: SRC-NARROW — source_ref too narrow for node content ---
        # Pattern 1: Node has both text AND operative_text, meaning its legal
        # content spans the opening phrase (text) and a continuation
        # (operative_text) that appears later in the source flow.
        # If source_ref only covers a single block, it can't be covering
        # the full legal unit.
        node_end = _source_ref_end_block(node)
        node_start = _source_ref_start_block(node)

        if (
            node.text
            and node.operative_text
            and node_start is not None
            and node_end is not None
            and node_start == node_end
            and source_ref.get("resolution") == "exact"
        ):
            result.findings.append(
                build_finding(
                    issue_id=f"SRC-NARROW-{node.node_id}",
                    category="source_refs",
                    severity="major",
                    title="Exact source_ref is too narrow for node with text + operative_text",
                    problem=(
                        f"The node has text ('{node.text[:60]}...') and operative_text "
                        f"('{node.operative_text[:60]}...'), but its source_ref only "
                        f"covers block {node_start}. The operative_text continuation "
                        f"must live in later source blocks."
                    ),
                    node=node,
                    raw_source_fragment=source_text(context, node),
                    why_real_defect=(
                        "A node with both text and operative_text represents a legal unit "
                        "where the opening phrase and its continuation are inseparable. "
                        "An exact source_ref covering only the opening block fails as a "
                        "source-faithful audit anchor."
                    ),
                    recommended_fix=(
                        "Extend the source_ref end_block to cover the continuation text, "
                        "or change the resolution from 'exact' to 'container' if the full "
                        "span cannot be precisely determined."
                    ),
                    confidence=0.92,
                )
            )

        # Pattern 2: Node's end_block is less than the max end_block of its children.
        # This means the parent's source_ref doesn't encompass all its children's content.
        child_ids = context.indexed_rule.children_map.get(node_id, [])
        if child_ids and node_end is not None:
            max_child_end = None
            for child_id in child_ids:
                child_node = context.indexed_rule.nodes.get(child_id)
                if child_node:
                    child_end = _source_ref_end_block(child_node)
                    if child_end is not None:
                        if max_child_end is None or child_end > max_child_end:
                            max_child_end = child_end
            if (
                max_child_end is not None
                and node_end < max_child_end
                and source_ref.get("resolution") == "exact"
                and node.operative_text
            ):
                result.findings.append(
                    build_finding(
                        issue_id=f"SRC-NARROW-CHILD-{node.node_id}",
                        category="source_refs",
                        severity="major",
                        title="Node source_ref does not encompass its children's source spans",
                        problem=(
                            f"The node's source_ref ends at block {node_end}, but its "
                            f"children extend to block {max_child_end}. The node also has "
                            f"operative_text that continues after the children."
                        ),
                        node=node,
                        raw_source_fragment=source_text(context, node),
                        why_real_defect=(
                            "A parent node with operative_text and children should have a "
                            "source_ref that encompasses both its children and the continuation "
                            "text. A narrow span breaks the audit trail for the full legal unit."
                        ),
                        recommended_fix=(
                            "Extend the node's source_ref to cover its full content span, "
                            "from start_block through at least the maximum child end_block "
                            "and the continuation text blocks."
                        ),
                        confidence=0.89,
                    )
                )

    return result

