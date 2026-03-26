from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


DossierKind = Literal["rule", "node", "table", "amendment", "cluster"]
DecisionLabel = Literal[
    "confirmed_issue",
    "acceptable_artifact",
    "needs_manual_review",
    "no_issue",
]
StageName = Literal["docket", "specialist", "skeptic", "arbiter"]
Severity = Literal["critical", "major", "moderate", "minor"]


class EvidenceLocator(BaseModel):
    source_name: str
    pointer: str
    start: Optional[int] = None
    end: Optional[int] = None


class EvidenceSnippet(BaseModel):
    kind: str
    label: str
    locator: EvidenceLocator
    text: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class Dossier(BaseModel):
    dossier_id: str
    kind: DossierKind
    domain: str
    target_id: str
    title: str
    category_focus: List[str] = Field(default_factory=list)
    candidate_fragment: Dict[str, Any] = Field(default_factory=dict)
    schema_excerpt: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[EvidenceSnippet] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CounselSpec(BaseModel):
    name: str
    stage: StageName
    categories: List[str]
    prompt_key: str


class CouncilTask(BaseModel):
    task_id: str
    stage: StageName
    counsel_name: str
    dossier_id: str
    prompt_key: str
    categories: List[str] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)


class Judgment(BaseModel):
    label: DecisionLabel
    counsel_name: str
    dossier_id: str
    category: Optional[str] = None
    node_id: Optional[str] = None
    severity: Optional[Severity] = None
    title: Optional[str] = None
    problem: Optional[str] = None
    evidence_refs: List[str] = Field(default_factory=list)
    recommended_fix: Optional[str] = None
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CouncilRunPlan(BaseModel):
    council_name: str
    domain: str
    shared_prefix: str
    dossiers: List[Dossier] = Field(default_factory=list)
    tasks: List[CouncilTask] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProviderMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ProviderRequest(BaseModel):
    model: str
    system_prompt: str
    messages: List[ProviderMessage] = Field(default_factory=list)
    max_tokens: int
    temperature: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CompiledTaskRequest(BaseModel):
    task_id: str
    stage: StageName
    counsel_name: str
    dossier_id: str
    categories: List[str] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)
    provider_request: ProviderRequest


class ProviderResponseBlock(BaseModel):
    kind: str
    text: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class ProviderUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


class ProviderResponse(BaseModel):
    model: str
    blocks: List[ProviderResponseBlock] = Field(default_factory=list)
    raw_response: Dict[str, Any] = Field(default_factory=dict)
    usage: ProviderUsage = Field(default_factory=ProviderUsage)
    stop_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutedTaskResult(BaseModel):
    task_id: str
    counsel_name: str
    dossier_id: str
    provider_response: ProviderResponse
    parsed_judgment: Optional[Judgment] = None
    parse_error: Optional[str] = None


class CandidateIssue(BaseModel):
    issue_id: str
    signature: str
    dossier_id: str
    node_id: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[Severity] = None
    title: Optional[str] = None
    problem: Optional[str] = None
    evidence_refs: List[str] = Field(default_factory=list)
    recommended_fix: Optional[str] = None
    supporting_task_ids: List[str] = Field(default_factory=list)
    supporting_counsel: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RuleSynthesisReport(BaseModel):
    rule_id: str
    status: Literal["clean", "issues_found", "needs_manual_review"]
    confirmed_issues: List[CandidateIssue] = Field(default_factory=list)
    accepted_artifacts: List[CandidateIssue] = Field(default_factory=list)
    manual_review_issues: List[CandidateIssue] = Field(default_factory=list)
    rejected_issues: List[CandidateIssue] = Field(default_factory=list)
    summary: str


class CouncilDeliberationRun(BaseModel):
    specialist_compiled_requests: List[CompiledTaskRequest] = Field(default_factory=list)
    specialist_results: List[ExecutedTaskResult] = Field(default_factory=list)
    candidate_issues: List[CandidateIssue] = Field(default_factory=list)
    challenge_compiled_requests: List[CompiledTaskRequest] = Field(default_factory=list)
    challenge_results: List[ExecutedTaskResult] = Field(default_factory=list)
    arbiter_compiled_requests: List[CompiledTaskRequest] = Field(default_factory=list)
    arbiter_results: List[ExecutedTaskResult] = Field(default_factory=list)
    rule_report: RuleSynthesisReport
