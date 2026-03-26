from pathlib import Path

from clanker_zone.domains.gst.corpus import discover_rule_bundles


def test_discover_rule_bundles_from_pc_corpus():
    bundles = discover_rule_bundles(Path("pc"))
    assert len(bundles) == 6
    rule_numbers = sorted(bundle.rule_json["metadata"]["rule_number"] for bundle in bundles)
    assert rule_numbers == ["26", "3", "4", "5", "6", "7"]
    bundle_26 = next(bundle for bundle in bundles if bundle.rule_json["metadata"]["rule_number"] == "26")
    assert bundle_26.raw_html_path is not None
    assert bundle_26.hint_path is not None

