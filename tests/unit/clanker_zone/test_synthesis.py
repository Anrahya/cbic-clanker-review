from clanker_zone.models import CandidateIssue, ExecutedTaskResult, Judgment, ProviderResponse
from clanker_zone.report.finalize import synthesize_rule_report


def test_synthesize_rule_report_uses_arbiter_outcome():
    issue = CandidateIssue(
        issue_id="ISSUE-0001",
        signature="sig",
        dossier_id="gst-node-CGST-R26(1)-P4",
        node_id="CGST-R26(1)-P4",
        category="amendment_markers",
        severity="major",
        title="Marker scope too broad",
        problem="The marker spans too much source text.",
    )
    challenge_result = ExecutedTaskResult(
        task_id="skeptic-ISSUE-0001",
        counsel_name="artifact_defender",
        dossier_id=issue.dossier_id,
        provider_response=ProviderResponse(model="fake", metadata={"payload": {"issue_id": "ISSUE-0001"}}),
        parsed_judgment=Judgment(
            label="needs_manual_review",
            counsel_name="artifact_defender",
            dossier_id=issue.dossier_id,
            category="amendment_markers",
            confidence=0.68,
            metadata={"issue_id": "ISSUE-0001"},
        ),
    )
    arbiter_result = ExecutedTaskResult(
        task_id="arbiter-ISSUE-0001",
        counsel_name="chief_arbiter",
        dossier_id=issue.dossier_id,
        provider_response=ProviderResponse(model="fake", metadata={"payload": {"issue_id": "ISSUE-0001"}}),
        parsed_judgment=Judgment(
            label="confirmed_issue",
            counsel_name="chief_arbiter",
            dossier_id=issue.dossier_id,
            category="amendment_markers",
            severity="major",
            confidence=0.9,
            metadata={"issue_id": "ISSUE-0001"},
        ),
    )

    report = synthesize_rule_report(
        rule_id="CGST-R26",
        issues=[issue],
        challenge_results=[challenge_result],
        arbiter_results=[arbiter_result],
    )

    assert report.status == "issues_found"
    assert [item.issue_id for item in report.confirmed_issues] == ["ISSUE-0001"]
    assert not report.manual_review_issues
