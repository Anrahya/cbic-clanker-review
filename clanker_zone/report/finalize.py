from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from ..models import CandidateIssue, ExecutedTaskResult, RuleSynthesisReport


def synthesize_rule_report(
    *,
    rule_id: str,
    issues: Iterable[CandidateIssue],
    challenge_results: List[ExecutedTaskResult],
    arbiter_results: List[ExecutedTaskResult],
) -> RuleSynthesisReport:
    issue_map: Dict[str, CandidateIssue] = {issue.issue_id: issue for issue in issues}
    challenge_index = _index_results_by_issue(challenge_results)
    arbiter_index = _index_results_by_issue(arbiter_results)

    confirmed: List[CandidateIssue] = []
    accepted: List[CandidateIssue] = []
    manual: List[CandidateIssue] = []
    rejected: List[CandidateIssue] = []

    for issue_id, issue in issue_map.items():
        arbiter = arbiter_index.get(issue_id)
        challenge = challenge_index.get(issue_id)
        if arbiter is not None and arbiter.parsed_judgment is not None:
            label = arbiter.parsed_judgment.label
        elif challenge is not None and challenge.parsed_judgment is not None:
            label = challenge.parsed_judgment.label
        else:
            label = "needs_manual_review"

        if label == "confirmed_issue":
            confirmed.append(issue)
        elif label == "needs_manual_review":
            manual.append(issue)
        elif label == "acceptable_artifact":
            accepted.append(issue)
        else:
            rejected.append(issue)

    if confirmed:
        status = "issues_found"
        summary = f"{len(confirmed)} confirmed issue(s) remain after challenge and arbitration."
    elif manual:
        status = "needs_manual_review"
        summary = f"No issue was confirmed, but {len(manual)} issue(s) still need manual review."
    else:
        status = "clean"
        summary = "No candidate issues survived challenge and arbitration."

    return RuleSynthesisReport(
        rule_id=rule_id,
        status=status,
        confirmed_issues=confirmed,
        accepted_artifacts=accepted,
        manual_review_issues=manual,
        rejected_issues=rejected,
        summary=summary,
    )


def _index_results_by_issue(results: List[ExecutedTaskResult]) -> Dict[str, ExecutedTaskResult]:
    index: Dict[str, ExecutedTaskResult] = {}
    for result in results:
        issue_id = _resolve_issue_id(result)
        if issue_id:
            index[issue_id] = result
    return index


def _resolve_issue_id(result: ExecutedTaskResult) -> Optional[str]:
    if result.parsed_judgment is not None:
        issue_id = result.parsed_judgment.metadata.get("issue_id")
        if issue_id:
            return str(issue_id)
    issue_id = result.provider_response.metadata.get("payload", {}).get("issue_id")
    if issue_id:
        return str(issue_id)
    if result.task_id.startswith("skeptic-") or result.task_id.startswith("arbiter-"):
        return result.task_id.split("-", 1)[1]
    return None
