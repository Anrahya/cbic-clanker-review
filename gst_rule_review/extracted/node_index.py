from __future__ import annotations

from typing import Any, Dict, Optional

from ..models import IndexedNode, IndexedRule
from .amendments import build_amendment_map


CHILD_KEYS = {
    "children",
    "nodes",
    "clauses",
    "sub_clauses",
    "sub_rules",
    "provisos",
    "explanations",
    "items",
    "rows",
}


def _get_node_id(node: Dict[str, Any], path: str) -> str:
    for key in ("node_id", "id", "uid"):
        if node.get(key):
            return str(node[key])
    return path.replace("$.", "").replace(".", "-").replace("[", "-").replace("]", "")


def _get_node_type(node: Dict[str, Any], path: str) -> str:
    for key in ("node_type", "type", "kind"):
        if node.get(key):
            return str(node[key])
    if path == "$":
        return "rule_document"
    return "node"


def _source_block_ids(source_ref: Any) -> list[int]:
    if isinstance(source_ref, dict):
        block_ids = source_ref.get("block_ids") or source_ref.get("blocks") or []
        return [int(block_id) for block_id in block_ids]
    if isinstance(source_ref, list):
        return [int(block_id) for block_id in source_ref]
    return []


def index_rule_json(rule_json: Dict[str, Any]) -> IndexedRule:
    indexed = IndexedRule(rule_json=rule_json, amendment_map=build_amendment_map(rule_json))

    def visit(value: Any, path: str, parent_id: Optional[str] = None) -> None:
        if isinstance(value, dict):
            has_node_shape = any(key in value for key in ("node_id", "id", "type", "node_type")) or (
                path == "$" or any(key in value for key in CHILD_KEYS)
            )
            current_parent_id = parent_id
            if has_node_shape:
                node_id = _get_node_id(value, path)
                node_type = _get_node_type(value, path)
                indexed_node = IndexedNode(
                    node_id=node_id,
                    json_path=path,
                    node_type=node_type,
                    parent_id=parent_id,
                    label=value.get("label"),
                    display_label=value.get("display_label"),
                    text=value.get("text"),
                    operative_text=value.get("operative_text"),
                    raw_text=value.get("raw_text"),
                    status=value.get("status"),
                    source_ref=value.get("source_ref"),
                    amendment_markers=[str(marker).strip("[]") for marker in value.get("amendment_markers", [])],
                    cross_refs=value.get("cross_refs", []),
                    effective_from=value.get("effective_from"),
                    effective_until=value.get("effective_until"),
                    node=value,
                )
                indexed.nodes[node_id] = indexed_node
                indexed.parent_map[node_id] = parent_id
                indexed.children_map.setdefault(node_id, [])
                indexed.path_index[path] = node_id
                if indexed_node.label:
                    indexed.label_index[indexed_node.label] = node_id
                indexed.type_index.setdefault(node_type, []).append(node_id)
                for marker in indexed_node.amendment_markers:
                    indexed.marker_to_nodes.setdefault(marker, []).append(node_id)
                indexed.source_block_coverage[node_id] = _source_block_ids(indexed_node.source_ref)
                if indexed.root_node_id is None:
                    indexed.root_node_id = node_id
                if parent_id:
                    indexed.children_map.setdefault(parent_id, []).append(node_id)
                current_parent_id = node_id
            for key, child in value.items():
                child_path = f"{path}.{key}" if path != "$" else f"$.{key}"
                if key in CHILD_KEYS and isinstance(child, list):
                    for idx, item in enumerate(child):
                        visit(item, f"{child_path}[{idx}]", current_parent_id)
                elif isinstance(child, dict):
                    visit(child, child_path, current_parent_id)
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                visit(item, f"{path}[{idx}]", parent_id)

    visit(rule_json, "$")
    return indexed
