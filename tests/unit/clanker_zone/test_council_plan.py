from pathlib import Path

from clanker_zone.config import CouncilConfig
from clanker_zone.council import CouncilBuilder
from clanker_zone.domains.gst.corpus import discover_rule_bundles
from clanker_zone.domains.gst.dossiers import build_gst_dossiers
from clanker_zone.domains.gst.policy import (
    GST_CONSTITUTION,
    GST_COUNSEL_ROSTER,
    GST_DOMAIN_OVERVIEW,
    GST_OUTPUT_CONTRACT,
)


def test_council_builder_creates_multistage_plan():
    bundles = discover_rule_bundles(Path("pc"))
    bundle = next(bundle for bundle in bundles if bundle.rule_json["metadata"]["rule_number"] == "26")
    dossiers = build_gst_dossiers(bundle)
    builder = CouncilBuilder(CouncilConfig(), "gst", GST_COUNSEL_ROSTER)
    plan = builder.build_plan(
        dossiers=dossiers[:5],
        constitution=GST_CONSTITUTION,
        domain_overview=GST_DOMAIN_OVERVIEW,
        output_contract=GST_OUTPUT_CONTRACT,
        metadata={"rule_number": "26"},
    )
    stages = {task.stage for task in plan.tasks}
    assert stages == {"arbiter", "docket", "skeptic", "specialist"}
    assert "GST rule extraction review" in plan.shared_prefix
    assert plan.metadata["rule_number"] == "26"

