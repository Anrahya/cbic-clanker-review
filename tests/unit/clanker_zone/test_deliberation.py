from clanker_zone.deliberation import build_issue_stage_tasks, compile_issue_requests
from clanker_zone.domains.gst.prompts import build_issue_task_prompt
from clanker_zone.models import (
    CandidateIssue,
    CounselSpec,
    CouncilRunPlan,
    Dossier,
    EvidenceLocator,
    EvidenceSnippet,
    ExecutedTaskResult,
    Judgment,
    ProviderMessage,
    ProviderRequest,
    ProviderResponse,
)


class FakeProvider:
    def build_request(self, *, system_prompt: str, user_prompt: str, metadata=None) -> ProviderRequest:
        return ProviderRequest(
            model="fake",
            system_prompt=system_prompt,
            messages=[ProviderMessage(role="user", content=user_prompt)],
            max_tokens=512,
            temperature=0.1,
            metadata=metadata or {},
        )

    def resolve_api_key(self) -> str:
        return "unused"

    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        raise AssertionError("invoke should not be called in prompt compilation test")


def test_compile_issue_requests_includes_issue_and_prior_judgments():
    dossier = Dossier(
        dossier_id="gst-node-CGST-R26(1)-P4",
        kind="node",
        domain="gst",
        target_id="CGST-R26(1)-P4",
        title="Node dossier",
        category_focus=["amendment_markers"],
        candidate_fragment={"id": "CGST-R26(1)-P4"},
        evidence=[
            EvidenceSnippet(
                kind="source_block",
                label="Source block 12",
                locator=EvidenceLocator(source_name="hint.source_blocks", pointer="order=12"),
                text="Provided that ...",
            )
        ],
        metadata={"json_path": "$.node.children[0]"},
    )
    plan = CouncilRunPlan(
        council_name="clanker zone",
        domain="gst",
        shared_prefix="constitution",
        dossiers=[dossier],
    )
    issue = CandidateIssue(
        issue_id="ISSUE-0001",
        signature="sig",
        dossier_id=dossier.dossier_id,
        node_id="CGST-R26(1)-P4",
        category="amendment_markers",
        severity="major",
        title="Marker scope too broad",
        problem="The marker spans the parent proviso instead of the nested text only.",
        evidence_refs=["source_block:12"],
        recommended_fix="Retarget the marker to the nested proviso span.",
        supporting_task_ids=["specialist-amendment"],
        supporting_counsel=["amendment_counsel"],
    )
    roster = [
        CounselSpec(
            name="artifact_defender",
            stage="skeptic",
            categories=["amendment_markers"],
            prompt_key="gst.artifact_defender",
        )
    ]
    specialist_result = ExecutedTaskResult(
        task_id="specialist-amendment",
        counsel_name="amendment_counsel",
        dossier_id=dossier.dossier_id,
        provider_response=ProviderResponse(model="fake"),
        parsed_judgment=Judgment(
            label="confirmed_issue",
            counsel_name="amendment_counsel",
            dossier_id=dossier.dossier_id,
            node_id="CGST-R26(1)-P4",
            category="amendment_markers",
            severity="major",
            title="Marker scope too broad",
            problem="The marker spans the parent proviso instead of the nested text only.",
            evidence_refs=["source_block:12"],
            recommended_fix="Retarget the marker to the nested proviso span.",
            confidence=0.93,
        ),
    )

    tasks = build_issue_stage_tasks(issues=[issue], roster=roster, stage="skeptic")
    compiled = compile_issue_requests(
        plan=plan,
        tasks=tasks,
        issues=[issue],
        prior_results=[specialist_result],
        provider=FakeProvider(),
        prompt_builder=build_issue_task_prompt,
    )

    assert len(compiled) == 1
    request = compiled[0]
    assert request.payload["issue_id"] == "ISSUE-0001"
    assert request.provider_request.metadata["payload"]["issue_id"] == "ISSUE-0001"
    assert '"candidate_issue"' in request.provider_request.messages[0].content
    assert '"prior_judgments"' in request.provider_request.messages[0].content
    assert "Marker scope too broad" in request.provider_request.messages[0].content
