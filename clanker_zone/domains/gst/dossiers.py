from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Set, Tuple

from ...models import Dossier, EvidenceLocator, EvidenceSnippet
from .corpus import GSTRuleBundle


NodePair = Tuple[Dict[str, Any], str]


def _walk_nodes(node: Dict[str, Any], path: str = "$.node") -> List[NodePair]:
    pairs: List[NodePair] = [(node, path)]
    for bucket in ("children", "provisos", "explanations"):
        for idx, child in enumerate(node.get(bucket, [])):
            pairs.extend(_walk_nodes(child, f"{path}.{bucket}[{idx}]"))
    return pairs


def _schema_excerpt(schema_json: Dict[str, Any], node_type: str) -> Dict[str, Any]:
    definitions = schema_json.get("definitions", {})
    node_def = definitions.get("node", {})
    excerpt = {
        "node_type": node_type,
        "required": node_def.get("required", []),
        "properties": {
            key: value
            for key, value in node_def.get("properties", {}).items()
            if key
            in {
                "label",
                "display_label",
                "type",
                "text",
                "raw_text",
                "operative_text",
                "children",
                "provisos",
                "explanations",
                "cross_refs",
                "source_ref",
                "amendment_markers",
                "effective_from",
                "effective_until",
                "status",
                "table_data",
                "formula_data",
            }
        },
    }
    return excerpt


def _focus_categories(node: Dict[str, Any]) -> List[str]:
    categories: set[str] = set()
    node_type = node.get("type")

    # Source fidelity: only when the node has text content to verify
    if node.get("text") or node.get("raw_text") or node.get("operative_text"):
        categories.add("text_fidelity")

    # Source refs: only when the node actually has a source_ref
    if node.get("source_ref"):
        categories.add("source_refs")

    # Structure/scope: clauses, sub-clauses, provisos, explanations
    if node_type in {"sub_rule", "clause", "sub_clause"}:
        categories.update({"structure_scope", "clauses"})
    if node_type in {"proviso", "explanation"}:
        categories.update({"provisos_explanations", "structure_scope"})

    # Tables: only when table evidence exists
    if node_type == "table" or node.get("table_data"):
        categories.add("tables")

    # Formulas
    if node.get("formula_data"):
        categories.add("formulas")

    # Amendment/chronology: only when amendment markers or non-active status
    if node.get("amendment_markers") or node.get("status") != "active":
        categories.update({"amendment_markers", "status_chronology"})

    # Cross-refs and duplicates: only when cross_refs exist
    if node.get("cross_refs"):
        categories.update({"cross_refs", "duplicates"})

    return sorted(categories)


def _target_card(node: Dict[str, Any], path: str, depth: int) -> EvidenceSnippet:
    source_ref = node.get("source_ref") or {}
    start = source_ref.get("start_block")
    end = source_ref.get("end_block")
    pointer = path
    if start and end:
        pointer = f"{path}::blocks={start}-{end}"
    return EvidenceSnippet(
        kind="target_card",
        label=f"Target node {node['id']}",
        locator=EvidenceLocator(
            source_name="rule_json",
            pointer=pointer,
            start=start,
            end=end,
        ),
        text=node.get("text") or node.get("raw_text") or node.get("title"),
        payload={
            "id": node["id"],
            "type": node.get("type"),
            "display_label": node.get("display_label"),
            "status": node.get("status"),
            "depth": depth,
            "amendment_markers": node.get("amendment_markers", []),
            "json_path": path,
        },
    )


def _descendant_span(node_pairs: List[NodePair]) -> Tuple[Optional[int], Optional[int]]:
    starts: List[int] = []
    ends: List[int] = []
    for node, _ in node_pairs:
        source_ref = node.get("source_ref") or {}
        start = source_ref.get("start_block")
        end = source_ref.get("end_block")
        if start:
            starts.append(start)
        if end:
            ends.append(end)
    if not starts or not ends:
        return None, None
    return min(starts), max(ends)


def _source_block_snippets_for_span(bundle: GSTRuleBundle, start: Optional[int], end: Optional[int]) -> List[EvidenceSnippet]:
    if not start or not end:
        return []
    snippets: List[EvidenceSnippet] = []
    for block in bundle.hint_json.get("source_blocks", []):
        order = block.get("order")
        if start <= order <= end:
            snippets.append(
                EvidenceSnippet(
                    kind="source_block",
                    label=f"Source block {order}",
                    locator=EvidenceLocator(source_name="hint.source_blocks", pointer=f"order={order}", start=order, end=order),
                    text=block.get("text"),
                    payload=block,
                )
            )
    return snippets


def _segment_snippets_for_span(bundle: GSTRuleBundle, cluster_root_id: str, start: Optional[int], end: Optional[int]) -> List[EvidenceSnippet]:
    if not start or not end:
        return []
    snippets: List[EvidenceSnippet] = []
    for segment in bundle.hint_json.get("segments", []):
        seg_start = segment.get("start_order")
        seg_end = segment.get("end_order")
        if not seg_start or not seg_end:
            continue
        if segment.get("expected_id") == cluster_root_id:
            snippets.append(
                EvidenceSnippet(
                    kind="segment",
                    label=f"Hint segment for {cluster_root_id}",
                    locator=EvidenceLocator(
                        source_name="hint.segments",
                        pointer=f"expected_id={cluster_root_id}",
                        start=seg_start,
                        end=seg_end,
                    ),
                    text=segment.get("text"),
                    payload=segment,
                )
            )
            continue
        if seg_start <= end and start <= seg_end:
            snippets.append(
                EvidenceSnippet(
                    kind="segment_context",
                    label=f"Overlapping segment {seg_start}-{seg_end}",
                    locator=EvidenceLocator(
                        source_name="hint.segments",
                        pointer=f"start_order={seg_start},end_order={seg_end}",
                        start=seg_start,
                        end=seg_end,
                    ),
                    text=segment.get("text"),
                    payload=segment,
                )
            )
    return snippets


def _amendment_snippets_for_cluster(
    bundle: GSTRuleBundle,
    node_pairs: List[NodePair],
    start: Optional[int],
    end: Optional[int],
) -> List[EvidenceSnippet]:
    snippets: List[EvidenceSnippet] = []
    markers: Set[str] = set()
    for node, _ in node_pairs:
        markers.update(str(marker) for marker in node.get("amendment_markers", []))
    for amendment in bundle.hint_json.get("amendments", []):
        marker = str(amendment.get("marker"))
        if marker in markers:
            snippets.append(
                EvidenceSnippet(
                    kind="hint_amendment",
                    label=f"Hint amendment marker {marker}",
                    locator=EvidenceLocator(source_name="hint.amendments", pointer=f"marker={marker}"),
                    text=amendment.get("text"),
                    payload=amendment,
                )
            )
    if not start or not end:
        return snippets
    for span in bundle.hint_json.get("amendment_spans", []):
        span_start = span.get("open_block")
        span_end = span.get("close_block")
        if not span_start or not span_end:
            continue
        if span_start <= end and start <= span_end:
            marker = str(span.get("marker"))
            snippets.append(
                EvidenceSnippet(
                    kind="amendment_span",
                    label=f"Amendment span marker {marker}",
                    locator=EvidenceLocator(
                        source_name="hint.amendment_spans",
                        pointer=f"marker={marker}",
                        start=span_start,
                        end=span_end,
                    ),
                    text=span.get("open_anchor_text"),
                    payload=span,
                )
            )
    return snippets


def _cluster_categories(node_pairs: List[NodePair]) -> List[str]:
    categories: Set[str] = set()
    for node, _ in node_pairs:
        categories.update(_focus_categories(node))
    return sorted(categories)


def _cluster_metadata(
    *,
    node_pairs: List[NodePair],
    cluster_root: Dict[str, Any],
    cluster_root_path: str,
    start_block: Optional[int],
    end_block: Optional[int],
) -> Dict[str, Any]:
    return {
        "cluster_root_id": cluster_root["id"],
        "cluster_root_type": cluster_root.get("type"),
        "cluster_root_path": cluster_root_path,
        "cluster_source_span": {"start_block": start_block, "end_block": end_block},
        "target_node_ids": [node["id"] for node, _ in node_pairs],
        "target_node_paths": {node["id"]: path for node, path in node_pairs},
    }


def _build_cluster_dossier(
    bundle: GSTRuleBundle,
    *,
    cluster_root: Dict[str, Any],
    cluster_root_path: str,
) -> Dossier:
    node_pairs = _walk_nodes(cluster_root, cluster_root_path)
    start_block, end_block = _descendant_span(node_pairs)
    evidence: List[EvidenceSnippet] = [
        EvidenceSnippet(
            kind="cluster_root",
            label=f"Cluster root {cluster_root['id']}",
            locator=EvidenceLocator(source_name="rule_json", pointer=cluster_root_path, start=start_block, end=end_block),
            text=cluster_root.get("text") or cluster_root.get("raw_text") or cluster_root.get("title"),
            payload={
                "id": cluster_root["id"],
                "type": cluster_root.get("type"),
                "display_label": cluster_root.get("display_label"),
                "status": cluster_root.get("status"),
            },
        )
    ]
    for depth, (node, path) in enumerate(node_pairs):
        evidence.append(_target_card(node, path, depth))
    evidence.extend(_source_block_snippets_for_span(bundle, start_block, end_block))
    evidence.extend(_segment_snippets_for_span(bundle, cluster_root["id"], start_block, end_block))
    evidence.extend(_amendment_snippets_for_cluster(bundle, node_pairs, start_block, end_block))
    metadata = _cluster_metadata(
        node_pairs=node_pairs,
        cluster_root=cluster_root,
        cluster_root_path=cluster_root_path,
        start_block=start_block,
        end_block=end_block,
    )
    if bundle.raw_html:
        evidence.append(
            EvidenceSnippet(
                kind="raw_rule_html",
                label="Full Raw HTML for the Rule",
                locator=EvidenceLocator(source_name="raw_html", pointer="entire_file"),
                text=bundle.raw_html,
            )
        )
    metadata.update(
        {
            "rule_path": bundle.rule_path,
            "rule_json_mtime": bundle.rule_metadata.get("mtime"),
            "rule_json_sha256": bundle.rule_metadata.get("sha256"),
            "raw_html_path": bundle.raw_html_path,
            "raw_html_mtime": bundle.raw_html_metadata.get("mtime"),
            "raw_html_sha256": bundle.raw_html_metadata.get("sha256"),
            "hint_path": bundle.hint_path,
            "hint_json_mtime": bundle.hint_metadata.get("mtime"),
            "hint_json_sha256": bundle.hint_metadata.get("sha256"),
            "cluster_strategy": "parent_cluster",
            "session_timestamp": time.time(),
        }
    )
    return Dossier(
        dossier_id=f"gst-cluster-{cluster_root['id']}",
        kind="cluster",
        domain="gst",
        target_id=cluster_root["id"],
        title=f"Cluster dossier for {cluster_root['id']}",
        category_focus=_cluster_categories(node_pairs),
        candidate_fragment=cluster_root,
        schema_excerpt=_schema_excerpt(bundle.rule_schema_json, cluster_root.get("type", "node")),
        evidence=evidence,
        metadata=metadata,
    )


def _should_include_rule_cluster(bundle: GSTRuleBundle, rule_root: Dict[str, Any]) -> bool:
    if rule_root.get("table_data") or rule_root.get("formula_data"):
        return True
    children = rule_root.get("children", [])
    if not children:
        return True
    if not any(child.get("type") == "sub_rule" for child in children):
        return True
    if not bundle.hint_json.get("segments"):
        return True
    return False


def _cluster_roots(bundle: GSTRuleBundle, rule_root: Dict[str, Any]) -> List[NodePair]:
    if _should_include_rule_cluster(bundle, rule_root):
        return [(rule_root, "$.node")]
    roots: List[NodePair] = []
    for idx, child in enumerate(rule_root.get("children", [])):
        child_path = f"$.node.children[{idx}]"
        roots.append((child, child_path))
    return roots


def build_gst_dossiers(
    bundle: GSTRuleBundle,
    heuristic_signals: Optional[List[EvidenceSnippet]] = None,
) -> List[Dossier]:
    dossiers: List[Dossier] = []
    rule_root = bundle.rule_json["node"]
    rule_id = rule_root["id"]

    for cluster_root, cluster_root_path in _cluster_roots(bundle, rule_root):
        dossier = _build_cluster_dossier(
            bundle,
            cluster_root=cluster_root,
            cluster_root_path=cluster_root_path,
        )
        # Inject heuristic signals relevant to nodes in this cluster
        if heuristic_signals:
            cluster_node_ids = _collect_node_ids(cluster_root)
            for signal in heuristic_signals:
                signal_node = signal.payload.get("node_id") if signal.payload else None
                if signal_node and signal_node in cluster_node_ids:
                    dossier.evidence.append(signal)
        dossiers.append(dossier)

    for amendment in bundle.hint_json.get("amendments", []):
        marker = str(amendment.get("marker"))
        dossiers.append(
            Dossier(
                dossier_id=f"gst-amendment-{rule_id}-{marker}",
                kind="amendment",
                domain="gst",
                target_id=marker,
                title=f"Amendment dossier for marker {marker}",
                category_focus=["amendment_markers", "status_chronology"],
                candidate_fragment=amendment,
                schema_excerpt={"definition": bundle.rule_schema_json.get("definitions", {}).get("amendment", {})},
                evidence=_build_amendment_evidence(amendment, marker, bundle),
                metadata={
                    "rule_id": rule_id,
                    "rule_path": bundle.rule_path,
                    "rule_json_mtime": bundle.rule_metadata.get("mtime"),
                    "rule_json_sha256": bundle.rule_metadata.get("sha256"),
                    "hint_path": bundle.hint_path,
                    "hint_json_mtime": bundle.hint_metadata.get("mtime"),
                    "hint_json_sha256": bundle.hint_metadata.get("sha256"),
                    "session_timestamp": __import__("time").time(),
                },
            )
        )
    return dossiers


def _collect_node_ids(node: Dict[str, Any]) -> Set[str]:
    """Collect all node IDs in a subtree."""
    ids: Set[str] = set()
    node_id = node.get("id")
    if node_id:
        ids.add(node_id)
    for bucket in ("children", "provisos", "explanations"):
        for child in node.get(bucket, []):
            ids.update(_collect_node_ids(child))
    return ids


def _build_amendment_evidence(amendment: Dict[str, Any], marker: str, bundle: GSTRuleBundle) -> List[EvidenceSnippet]:
    evidence = [
        EvidenceSnippet(
            kind="hint_amendment",
            label=f"Hint amendment {marker}",
            locator=EvidenceLocator(source_name="hint.amendments", pointer=f"marker={marker}"),
            text=amendment.get("text"),
            payload=amendment,
        )
    ]
    if bundle.raw_html:
        evidence.append(
            EvidenceSnippet(
                kind="raw_rule_html",
                label="Full Raw HTML for the Rule",
                locator=EvidenceLocator(source_name="raw_html", pointer="entire_file"),
                text=bundle.raw_html,
            )
        )
    return evidence
