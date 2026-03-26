from __future__ import annotations

from typing import List, Optional

from .deliberation import build_issue_stage_tasks, compile_issue_requests
from .issues import aggregate_candidate_issues
from .models import CouncilDeliberationRun, CouncilRunPlan
from .report.finalize import synthesize_rule_report
from .session import compile_plan_requests, execute_compiled_requests


def run_issue_council(
    *,
    plan: CouncilRunPlan,
    roster,
    provider,
    specialist_prompt_builder,
    issue_prompt_builder,
    specialist_counsel_names: Optional[List[str]] = None,
    max_concurrency: int = 1,
) -> CouncilDeliberationRun:
    specialist_tasks = [
        task
        for task in plan.tasks
        if task.stage == "specialist"
        and (specialist_counsel_names is None or task.counsel_name in specialist_counsel_names)
    ]
    specialist_plan = plan.model_copy(update={"tasks": specialist_tasks})
    specialist_compiled = compile_plan_requests(
        plan=specialist_plan,
        provider=provider,
        prompt_builder=specialist_prompt_builder,
    )
    specialist_results = execute_compiled_requests(
        compiled_requests=specialist_compiled,
        provider=provider,
        max_concurrency=max_concurrency,
    )

    candidate_issues = aggregate_candidate_issues(specialist_results)
    challenge_tasks = build_issue_stage_tasks(issues=candidate_issues, roster=roster, stage="skeptic")
    challenge_compiled = compile_issue_requests(
        plan=plan,
        tasks=challenge_tasks,
        issues=candidate_issues,
        prior_results=specialist_results,
        provider=provider,
        prompt_builder=issue_prompt_builder,
    )
    challenge_results = execute_compiled_requests(
        compiled_requests=challenge_compiled,
        provider=provider,
        max_concurrency=max_concurrency,
    )

    arbiter_tasks = build_issue_stage_tasks(issues=candidate_issues, roster=roster, stage="arbiter")
    arbiter_compiled = compile_issue_requests(
        plan=plan,
        tasks=arbiter_tasks,
        issues=candidate_issues,
        prior_results=[*specialist_results, *challenge_results],
        provider=provider,
        prompt_builder=issue_prompt_builder,
    )
    arbiter_results = execute_compiled_requests(
        compiled_requests=arbiter_compiled,
        provider=provider,
        max_concurrency=max_concurrency,
    )

    rule_number = str(plan.metadata.get("rule_number") or plan.metadata.get("rule_id") or "unknown")
    rule_report = synthesize_rule_report(
        rule_id=rule_number if rule_number.startswith("CGST-") else f"CGST-R{rule_number}",
        issues=candidate_issues,
        challenge_results=challenge_results,
        arbiter_results=arbiter_results,
    )
    return CouncilDeliberationRun(
        specialist_compiled_requests=specialist_compiled,
        specialist_results=specialist_results,
        candidate_issues=candidate_issues,
        challenge_compiled_requests=challenge_compiled,
        challenge_results=challenge_results,
        arbiter_compiled_requests=arbiter_compiled,
        arbiter_results=arbiter_results,
        rule_report=rule_report,
    )
