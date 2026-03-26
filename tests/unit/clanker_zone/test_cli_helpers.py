from types import SimpleNamespace

from clanker_zone.cli import _select_dossiers


def test_select_dossiers_zero_limit_means_all():
    dossiers = [
        SimpleNamespace(dossier_id="d1", target_id="n1"),
        SimpleNamespace(dossier_id="d2", target_id="n2"),
    ]

    selected = _select_dossiers(dossiers, target_id=None, dossier_limit=0)

    assert selected == dossiers


def test_select_dossiers_matches_leaf_target_inside_cluster():
    dossiers = [
        SimpleNamespace(dossier_id="gst-cluster-parent", target_id="CGST-R26(1)", metadata={"target_node_ids": ["CGST-R26(1)", "CGST-R26(1)-P4"]}),
        SimpleNamespace(dossier_id="gst-amendment-1", target_id="1", metadata={}),
    ]

    selected = _select_dossiers(dossiers, target_id="CGST-R26(1)-P4", dossier_limit=0)

    assert [item.dossier_id for item in selected] == ["gst-cluster-parent"]
