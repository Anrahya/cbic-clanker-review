from clanker_zone.domains.gst.false_positive_filter import apply_gst_false_positive_filter
from clanker_zone.models import CandidateIssue, Dossier, EvidenceLocator, EvidenceSnippet, RuleSynthesisReport


def test_gst_false_positive_filter_downgrades_anchor_text_and_target_id_issues():
    dossier = Dossier(
        dossier_id="gst-node-CGST-R26(2)(e)",
        kind="node",
        domain="gst",
        target_id="CGST-R26(2)(e)",
        title="Node dossier",
        candidate_fragment={
            "id": "CGST-R26(2)(e)",
            "display_label": "(e)",
        },
    )
    report = RuleSynthesisReport(
        rule_id="CGST-R26",
        status="issues_found",
        confirmed_issues=[
            CandidateIssue(
                issue_id="ISSUE-1",
                signature="sig-1",
                dossier_id=dossier.dossier_id,
                node_id="CGST-R26(2)(e)",
                category="source_ref",
                severity="minor",
                title="anchor_text missing clause label prefix",
                problem="The source_ref anchor_text omits (e).",
            ),
            CandidateIssue(
                issue_id="ISSUE-2",
                signature="sig-2",
                dossier_id=dossier.dossier_id,
                node_id="CGST-R26(1)-P2",
                category="cross_refs",
                severity="minor",
                title="Missing target_id for external_act cross-reference",
                problem="The cross_ref target_id is null for an external_act.",
            ),
        ],
        summary="raw",
    )

    filtered = apply_gst_false_positive_filter(report=report, dossiers=[dossier])

    assert filtered.status == "clean"
    assert not filtered.confirmed_issues
    assert [item.issue_id for item in filtered.accepted_artifacts] == ["ISSUE-1", "ISSUE-2"]


def test_gst_false_positive_filter_downgrades_missing_effective_from_to_manual_review():
    dossier = Dossier(
        dossier_id="gst-node-CGST-R26(1)-P4",
        kind="node",
        domain="gst",
        target_id="CGST-R26(1)-P4",
        title="Node dossier",
        candidate_fragment={"id": "CGST-R26(1)-P4"},
    )
    report = RuleSynthesisReport(
        rule_id="CGST-R26",
        status="issues_found",
        confirmed_issues=[
            CandidateIssue(
                issue_id="ISSUE-7",
                signature="sig-7",
                dossier_id=dossier.dossier_id,
                node_id="CGST-R26(1)-P4",
                category="structure_scope",
                severity="minor",
                title="Missing effective_from despite inserted status",
                problem="The node has enacted_date evidence but no explicit effective_from.",
            )
        ],
        summary="raw",
    )

    filtered = apply_gst_false_positive_filter(report=report, dossiers=[dossier])

    assert filtered.status == "needs_manual_review"
    assert not filtered.confirmed_issues
    assert [item.issue_id for item in filtered.manual_review_issues] == ["ISSUE-7"]


def test_gst_false_positive_filter_allows_carry_in_amendment_span_artifacts():
    rule_dossier = Dossier(
        dossier_id="gst-node-CGST-R26",
        kind="node",
        domain="gst",
        target_id="CGST-R26",
        title="Rule dossier",
        candidate_fragment={"id": "CGST-R26"},
    )
    dossier = Dossier(
        dossier_id="gst-node-CGST-R26(1)-P3",
        kind="node",
        domain="gst",
        target_id="CGST-R26(1)-P3",
        title="Node dossier",
        candidate_fragment={
            "id": "CGST-R26(1)-P3",
            "source_ref": {"start_block": 5, "end_block": 5},
        },
        evidence=[
            EvidenceSnippet(
                kind="amendment_span",
                label="Amendment span marker 2",
                locator=EvidenceLocator(source_name="hint.amendment_spans", pointer="marker=2"),
                payload={"open_block": 4, "close_block": 5},
            )
        ],
    )
    report = RuleSynthesisReport(
        rule_id="CGST-R26",
        status="issues_found",
        confirmed_issues=[
            CandidateIssue(
                issue_id="ISSUE-BRACKET",
                signature="sig-b",
                dossier_id=rule_dossier.dossier_id,
                node_id="CGST-R26(1)-P3",
                category="text_fidelity",
                severity="minor",
                title="Bracket artifact in raw_text",
                problem="The node ends with a trailing bracket because the amendment span closes here.",
            ),
            CandidateIssue(
                issue_id="ISSUE-MARKER",
                signature="sig-m",
                dossier_id=dossier.dossier_id,
                node_id="CGST-R26(1)-P3",
                category="amendment_markers",
                severity="major",
                title="Incorrect amendment marker assigned to sibling proviso",
                problem="The marker only closes here because the bracket span crosses sibling boundaries.",
            ),
        ],
        summary="raw",
    )

    filtered = apply_gst_false_positive_filter(report=report, dossiers=[rule_dossier, dossier])

    assert filtered.status == "clean"
    assert not filtered.confirmed_issues
    assert [item.issue_id for item in filtered.accepted_artifacts] == ["ISSUE-BRACKET", "ISSUE-MARKER"]
