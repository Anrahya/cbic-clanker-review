from pathlib import Path

from clanker_zone.domains.gst.corpus import discover_rule_bundles
from clanker_zone.domains.gst.dossiers import build_gst_dossiers


def test_build_gst_dossiers_contains_cluster_and_amendment_packets():
    bundles = discover_rule_bundles(Path("pc"))
    bundle_26 = next(bundle for bundle in bundles if bundle.rule_json["metadata"]["rule_number"] == "26")
    dossiers = build_gst_dossiers(bundle_26)
    dossier_ids = {dossier.dossier_id for dossier in dossiers}
    assert "gst-cluster-CGST-R26(1)" in dossier_ids
    assert "gst-cluster-CGST-R26(2)" in dossier_ids
    assert "gst-amendment-CGST-R26-1" in dossier_ids
    cluster = next(dossier for dossier in dossiers if dossier.dossier_id == "gst-cluster-CGST-R26(1)")
    assert "CGST-R26(1)-P4" in cluster.metadata["target_node_ids"]
    assert "amendment_markers" in cluster.category_focus
    assert any(snippet.kind == "source_block" for snippet in cluster.evidence)
    assert any(snippet.kind == "target_card" and snippet.payload["id"] == "CGST-R26(1)-P4" for snippet in cluster.evidence)
    assert any(snippet.kind in {"segment", "segment_context"} for snippet in cluster.evidence)
