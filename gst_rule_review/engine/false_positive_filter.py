from __future__ import annotations

from ..models import Finding, LikelyFalsePositive


def filter_findings(
    findings: list[Finding],
    likely_false_positives: list[LikelyFalsePositive],
    tolerate_spacing_artifacts: bool,
    min_confirm_confidence: float,
) -> tuple[list[Finding], list[LikelyFalsePositive]]:
    confirmed: list[Finding] = []
    false_positive_bucket = list(likely_false_positives)
    seen_issue_ids: set[str] = set()
    for finding in findings:
        if finding.issue_id in seen_issue_ids:
            continue
        seen_issue_ids.add(finding.issue_id)
        if finding.confidence < min_confirm_confidence:
            false_positive_bucket.append(
                LikelyFalsePositive(
                    title=finding.title,
                    reason="Confidence is below the confirmation threshold, so the issue is retained only as a likely false positive or manual-review candidate.",
                    raw_source_fragment=finding.raw_source_fragment,
                    json_fragment=finding.json_fragment,
                )
            )
            continue
        if tolerate_spacing_artifacts and finding.category == "text_fidelity" and "spacing" in finding.problem.lower():
            false_positive_bucket.append(
                LikelyFalsePositive(
                    title=finding.title,
                    reason="The difference is treated as a harmless CBIC formatting artifact under the active config.",
                    raw_source_fragment=finding.raw_source_fragment,
                    json_fragment=finding.json_fragment,
                )
            )
            continue
        confirmed.append(finding)
    return confirmed, false_positive_bucket

