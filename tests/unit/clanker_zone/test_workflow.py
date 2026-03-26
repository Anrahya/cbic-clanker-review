from typing import Optional

from clanker_zone.models import (
    CounselSpec,
    CouncilRunPlan,
    CouncilTask,
    Dossier,
    EvidenceLocator,
    EvidenceSnippet,
    ProviderMessage,
    ProviderRequest,
    ProviderResponse,
    ProviderResponseBlock,
)
from clanker_zone.workflow import run_issue_council


class QueueProvider:
    def __init__(self, responses):
        self._responses = list(responses)

    def build_request(self, *, system_prompt: str, user_prompt: str, metadata: Optional[dict] = None) -> ProviderRequest:
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
        text = self._responses.pop(0)
        return ProviderResponse(
            model="fake",
            blocks=[ProviderResponseBlock(kind="text", text=text)],
        )


def _specialist_prompt(prompt_key, dossier, categories):
    return '{"stage":"specialist","dossier_id":"%s"}' % dossier.dossier_id


def _issue_prompt(prompt_key, dossier, issue, prior_judgments):
    return '{"stage":"%s","issue_id":"%s","prior_count":%d}' % (prompt_key, issue.issue_id, len(prior_judgments))


def test_run_issue_council_executes_specialist_challenge_and_arbiter_stages():
    dossier = Dossier(
        dossier_id="gst-node-CGST-R8(4A)",
        kind="node",
        domain="gst",
        target_id="CGST-R8(4A)",
        title="Node dossier",
        category_focus=["text_fidelity"],
        candidate_fragment={"id": "CGST-R8(4A)"},
        evidence=[
            EvidenceSnippet(
                kind="candidate_node",
                label="Candidate node",
                locator=EvidenceLocator(source_name="rule_json", pointer="$.node.children[0]"),
                text="demo",
            )
        ],
    )
    plan = CouncilRunPlan(
        council_name="clanker zone",
        domain="gst",
        shared_prefix="constitution",
        dossiers=[dossier],
        tasks=[
            CouncilTask(
                task_id="specialist-source_fidelity-gst-node-CGST-R8(4A)",
                stage="specialist",
                counsel_name="source_fidelity_counsel",
                dossier_id=dossier.dossier_id,
                prompt_key="gst.source_fidelity",
                categories=["text_fidelity"],
                payload={"target_id": dossier.target_id},
            )
        ],
        metadata={"rule_number": "8"},
    )
    roster = [
        CounselSpec(
            name="artifact_defender",
            stage="skeptic",
            categories=["text_fidelity"],
            prompt_key="gst.artifact_defender",
        ),
        CounselSpec(
            name="chief_arbiter",
            stage="arbiter",
            categories=["text_fidelity"],
            prompt_key="gst.arbiter",
        ),
    ]
    provider = QueueProvider(
        [
            '{"label":"confirmed_issue","category":"text_fidelity","node_id":"CGST-R8(4A)","severity":"major","title":"Text is truncated","problem":"The node ends mid-sentence.","evidence_refs":["source_block:1"],"recommended_fix":"Restore the omitted text.","confidence":0.95}',
            '{"label":"needs_manual_review","category":"text_fidelity","node_id":"CGST-R8(4A)","severity":"major","title":"Text is truncated","problem":"The node ends mid-sentence.","evidence_refs":["source_block:1"],"recommended_fix":"Check whether the truncation is just a CBIC artifact.","confidence":0.6}',
            '{"label":"confirmed_issue","category":"text_fidelity","node_id":"CGST-R8(4A)","severity":"major","title":"Text is truncated","problem":"The node ends mid-sentence.","evidence_refs":["source_block:1"],"recommended_fix":"Restore the omitted text.","confidence":0.91}',
        ]
    )

    run = run_issue_council(
        plan=plan,
        roster=roster,
        provider=provider,
        specialist_prompt_builder=_specialist_prompt,
        issue_prompt_builder=_issue_prompt,
    )

    assert len(run.specialist_results) == 1
    assert len(run.candidate_issues) == 1
    assert len(run.challenge_results) == 1
    assert len(run.arbiter_results) == 1
    assert run.rule_report.status == "issues_found"
    assert run.rule_report.confirmed_issues[0].issue_id == "ISSUE-0001"
