from clanker_zone.issues import aggregate_candidate_issues
from clanker_zone.models import ExecutedTaskResult, Judgment, ProviderResponse


def test_aggregate_candidate_issues_merges_duplicate_findings():
    results = [
        ExecutedTaskResult(
            task_id="specialist-a",
            counsel_name="source_fidelity_counsel",
            dossier_id="gst-node-1",
            provider_response=ProviderResponse(model="fake"),
            parsed_judgment=Judgment(
                label="confirmed_issue",
                counsel_name="source_fidelity_counsel",
                dossier_id="gst-node-1",
                node_id="CGST-R8(4A)",
                category="text_fidelity",
                severity="moderate",
                title="Text is truncated",
                problem="The extracted node stops mid-sentence.",
                evidence_refs=["source_block:12"],
                recommended_fix="Restore the missing trailing text.",
                confidence=0.94,
            ),
        ),
        ExecutedTaskResult(
            task_id="specialist-b",
            counsel_name="structure_scope_counsel",
            dossier_id="gst-node-1",
            provider_response=ProviderResponse(model="fake"),
            parsed_judgment=Judgment(
                label="confirmed_issue",
                counsel_name="structure_scope_counsel",
                dossier_id="gst-node-1",
                node_id="CGST-R8(4A)",
                category="text_fidelity",
                severity="major",
                title="Text is truncated",
                problem="The extracted node stops mid-sentence.",
                evidence_refs=["source_block:13"],
                recommended_fix="Restore the missing trailing text.",
                confidence=0.88,
            ),
        ),
    ]

    issues = aggregate_candidate_issues(results)

    assert len(issues) == 1
    issue = issues[0]
    assert issue.severity == "major"
    assert issue.supporting_task_ids == ["specialist-a", "specialist-b"]
    assert issue.supporting_counsel == ["source_fidelity_counsel", "structure_scope_counsel"]
    assert issue.evidence_refs == ["source_block:12", "source_block:13"]
