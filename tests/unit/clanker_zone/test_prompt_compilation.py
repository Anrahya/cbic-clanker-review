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
from clanker_zone.domains.gst.prompts import build_task_prompt
from clanker_zone.provider.minimax import MiniMaxProvider, MiniMaxProviderConfig
from clanker_zone.session import compile_plan_requests


def test_compile_plan_requests_builds_minimax_ready_payloads():
    bundles = discover_rule_bundles(Path("pc"))
    bundle = next(bundle for bundle in bundles if bundle.rule_json["metadata"]["rule_number"] == "26")
    dossiers = build_gst_dossiers(bundle)[:3]
    builder = CouncilBuilder(CouncilConfig(), "gst", GST_COUNSEL_ROSTER)
    plan = builder.build_plan(
        dossiers=dossiers,
        constitution=GST_CONSTITUTION,
        domain_overview=GST_DOMAIN_OVERVIEW,
        output_contract=GST_OUTPUT_CONTRACT,
        metadata={"rule_number": "26"},
    )
    provider = MiniMaxProvider(MiniMaxProviderConfig())
    compiled = compile_plan_requests(plan=plan, provider=provider, prompt_builder=build_task_prompt)
    assert compiled
    first = compiled[0]
    assert first.provider_request.model == "MiniMax-M2.7"
    assert first.provider_request.system_prompt.startswith("You are part of Clanker Zone")
    assert first.provider_request.metadata["task_id"] == first.task_id
    assert '"dossier_id"' in first.provider_request.messages[0].content
