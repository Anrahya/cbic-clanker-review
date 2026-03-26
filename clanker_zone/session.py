from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, List, Optional, Tuple

from .models import CompiledTaskRequest, CouncilRunPlan, Dossier, ExecutedTaskResult, Judgment
from .parser import parse_judgment_response
from .provider.base import LLMProvider


PromptBuilder = Callable[[str, Dossier, list[str]], str]


def compile_plan_requests(
    *,
    plan: CouncilRunPlan,
    provider: LLMProvider,
    prompt_builder: PromptBuilder,
) -> List[CompiledTaskRequest]:
    dossier_map: Dict[str, Dossier] = {dossier.dossier_id: dossier for dossier in plan.dossiers}
    compiled: List[CompiledTaskRequest] = []
    for task in plan.tasks:
        dossier = dossier_map[task.dossier_id]
        user_prompt = prompt_builder(task.prompt_key, dossier, task.categories)
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


def execute_compiled_requests(
    *,
    compiled_requests: List[CompiledTaskRequest],
    provider: LLMProvider,
    max_concurrency: int = 1,
) -> List[ExecutedTaskResult]:
    if max_concurrency <= 1:
        return [_execute_one(compiled, provider) for compiled in compiled_requests]

    indexed_results: List[Tuple[int, ExecutedTaskResult]] = []
    with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        future_map = {
            executor.submit(_execute_one, compiled, provider): index
            for index, compiled in enumerate(compiled_requests)
        }
        for future in as_completed(future_map):
            indexed_results.append((future_map[future], future.result()))
    indexed_results.sort(key=lambda item: item[0])
    return [result for _, result in indexed_results]


def _execute_one(compiled: CompiledTaskRequest, provider: LLMProvider) -> ExecutedTaskResult:
    response = provider.invoke(compiled.provider_request)
    response.metadata = {
        **compiled.provider_request.metadata,
        **response.metadata,
    }
    judgment: Optional[Judgment] = None
    parse_error: Optional[str] = None
    try:
        judgment = parse_judgment_response(
            response,
            counsel_name=compiled.counsel_name,
            dossier_id=compiled.dossier_id,
        )
        judgment.metadata.setdefault("task_id", compiled.task_id)
        judgment.metadata.setdefault("stage", compiled.stage)
        judgment.metadata.setdefault("categories", compiled.categories)
        judgment.metadata.setdefault("task_payload", compiled.payload)
        issue_id = compiled.payload.get("issue_id")
        if issue_id is not None:
            judgment.metadata.setdefault("issue_id", issue_id)
    except Exception as exc:  # parser failure should not drop raw response
        parse_error = str(exc)
    return ExecutedTaskResult(
        task_id=compiled.task_id,
        counsel_name=compiled.counsel_name,
        dossier_id=compiled.dossier_id,
        provider_response=response,
        parsed_judgment=judgment,
        parse_error=parse_error,
    )
