from __future__ import annotations

from typing import Callable, Dict, Iterable, List

from .models import CandidateIssue, CompiledTaskRequest, CouncilRunPlan, CouncilTask, Dossier, ExecutedTaskResult, Judgment
from .provider.base import LLMProvider


IssuePromptBuilder = Callable[[str, Dossier, CandidateIssue, List[Judgment]], str]


def build_issue_stage_tasks(
    *,
    issues: Iterable[CandidateIssue],
    roster,
    stage: str,
) -> List[CouncilTask]:
    counsel = next((item for item in roster if item.stage == stage), None)
    if counsel is None:
        return []
    prompt_key = {"skeptic": "gst.challenge_issue", "arbiter": "gst.arbitrate_issue"}[stage]
    tasks: List[CouncilTask] = []
    for issue in issues:
        tasks.append(
            CouncilTask(
                task_id=f"{stage}-{issue.issue_id}",
                stage=stage,
                counsel_name=counsel.name,
                dossier_id=issue.dossier_id,
                prompt_key=prompt_key,
                categories=[issue.category] if issue.category else [],
                payload={
                    "issue_id": issue.issue_id,
                    "issue_signature": issue.signature,
                    "source_dossier_id": issue.dossier_id,
                    "node_id": issue.node_id,
                    "kind": "candidate_issue",
                },
            )
        )
    return tasks


def compile_issue_requests(
    *,
    plan: CouncilRunPlan,
    tasks: List[CouncilTask],
    issues: Iterable[CandidateIssue],
    prior_results: List[ExecutedTaskResult],
    provider: LLMProvider,
    prompt_builder: IssuePromptBuilder,
) -> List[CompiledTaskRequest]:
    dossier_map: Dict[str, Dossier] = {dossier.dossier_id: dossier for dossier in plan.dossiers}
    issue_map: Dict[str, CandidateIssue] = {issue.issue_id: issue for issue in issues}
    judgment_index = _index_prior_judgments(prior_results)
    task_judgment_index = {
        result.task_id: result.parsed_judgment
        for result in prior_results
        if result.parsed_judgment is not None
    }
    compiled: List[CompiledTaskRequest] = []
    for task in tasks:
        issue_id = str(task.payload["issue_id"])
        issue = issue_map[issue_id]
        dossier = dossier_map[task.dossier_id]
        prior_judgments = list(judgment_index.get(issue_id, []))
        for task_id in issue.supporting_task_ids:
            judgment = task_judgment_index.get(task_id)
            if judgment is not None:
                prior_judgments.append(judgment)
        prior_judgments = _dedupe_judgments(prior_judgments)
        user_prompt = prompt_builder(task.prompt_key, dossier, issue, prior_judgments)
        request = provider.build_request(
            system_prompt=plan.shared_prefix,
            user_prompt=user_prompt,
            metadata={
                "task_id": task.task_id,
                "counsel_name": task.counsel_name,
                "dossier_id": task.dossier_id,
                "stage": task.stage,
                "categories": task.categories,
                "payload": task.payload,
            },
        )
        compiled.append(
            CompiledTaskRequest(
                task_id=task.task_id,
                stage=task.stage,
                counsel_name=task.counsel_name,
                dossier_id=task.dossier_id,
                categories=task.categories,
                payload=task.payload,
                provider_request=request,
            )
        )
    return compiled


def _index_prior_judgments(results: List[ExecutedTaskResult]) -> Dict[str, List[Judgment]]:
    judgments_by_issue: Dict[str, List[Judgment]] = {}
    for result in results:
        judgment = result.parsed_judgment
        if judgment is None:
            continue
        issue_id = judgment.metadata.get("issue_id")
        if issue_id:
            judgments_by_issue.setdefault(str(issue_id), []).append(judgment)
        task_issue_id = result.provider_response.metadata.get("payload", {}).get("issue_id")
        if task_issue_id:
            judgments_by_issue.setdefault(str(task_issue_id), []).append(judgment)
    for issue_id, judgments in list(judgments_by_issue.items()):
        judgments_by_issue[issue_id] = _dedupe_judgments(judgments)
    return judgments_by_issue


def _dedupe_judgments(judgments: List[Judgment]) -> List[Judgment]:
    seen = set()
    unique: List[Judgment] = []
    for judgment in judgments:
        signature = (
            judgment.counsel_name,
            judgment.label,
            judgment.title,
            judgment.problem,
            judgment.metadata.get("task_id"),
        )
        if signature in seen:
            continue
        seen.add(signature)
        unique.append(judgment)
    return unique
