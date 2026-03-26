from typing import Optional

from clanker_zone.config import CouncilConfig
from clanker_zone.council import CouncilBuilder
from clanker_zone.models import (
    CounselSpec,
    Dossier,
    EvidenceLocator,
    EvidenceSnippet,
    ProviderMessage,
    ProviderRequest,
    ProviderResponse,
    ProviderResponseBlock,
)
from clanker_zone.session import compile_plan_requests, execute_compiled_requests


class FakeProvider:
    def build_request(self, *, system_prompt: str, user_prompt: str, metadata: Optional[dict] = None) -> ProviderRequest:
        return ProviderRequest(
            model="fake",
            system_prompt=system_prompt,
            messages=[ProviderMessage(role="user", content=user_prompt)],
            max_tokens=128,
            temperature=0.1,
            metadata=metadata or {},
        )

    def resolve_api_key(self) -> str:
        return "unused"

    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(
            model="fake",
            blocks=[
                ProviderResponseBlock(
                    kind="text",
                    text='{"label":"no_issue","category":null,"confidence":0.92}',
                )
            ],
        )


def test_execute_compiled_requests_parses_judgments():
    roster = [CounselSpec(name="demo", stage="specialist", categories=["text_fidelity"], prompt_key="demo")]
    dossier = Dossier(
        dossier_id="d1",
        kind="node",
        domain="gst",
        target_id="n1",
        title="Demo dossier",
        category_focus=["text_fidelity"],
        evidence=[
            EvidenceSnippet(
                kind="candidate",
                label="candidate",
                locator=EvidenceLocator(source_name="demo", pointer="x"),
                text="hello",
            )
        ],
    )
    builder = CouncilBuilder(CouncilConfig(), "gst", roster)
    plan = builder.build_plan(
        dossiers=[dossier],
        constitution="constitution",
        domain_overview="overview",
        output_contract="contract",
    )
    provider = FakeProvider()
    compiled = compile_plan_requests(
        plan=plan,
        provider=provider,
        prompt_builder=lambda prompt_key, dossier, categories: '{"demo":true}',
    )
    results = execute_compiled_requests(compiled_requests=compiled, provider=provider)
    assert results
    assert results[0].parsed_judgment is not None
    assert results[0].parsed_judgment.label == "no_issue"


class ErrorProvider(FakeProvider):
    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        raise RuntimeError("boom")


def test_execute_compiled_requests_captures_invoke_errors():
    roster = [CounselSpec(name="demo", stage="specialist", categories=["text_fidelity"], prompt_key="demo")]
    dossier = Dossier(
        dossier_id="d1",
        kind="node",
        domain="gst",
        target_id="n1",
        title="Demo dossier",
        category_focus=["text_fidelity"],
        evidence=[
            EvidenceSnippet(
                kind="candidate",
                label="candidate",
                locator=EvidenceLocator(source_name="demo", pointer="x"),
                text="hello",
            )
        ],
    )
    builder = CouncilBuilder(CouncilConfig(), "gst", roster)
    plan = builder.build_plan(
        dossiers=[dossier],
        constitution="constitution",
        domain_overview="overview",
        output_contract="contract",
    )
    provider = ErrorProvider()
    compiled = compile_plan_requests(
        plan=plan,
        provider=provider,
        prompt_builder=lambda prompt_key, dossier, categories: '{"demo":true}',
    )
    results = execute_compiled_requests(compiled_requests=compiled, provider=provider)

    assert results
    assert results[0].parsed_judgment is None
    assert results[0].invoke_error == "boom"
