from pathlib import Path

from gst_rule_review.engine.run_review import review_rule
from gst_rule_review.loader import load_json, load_text


def _review(rule_name: str):
    rule = load_json(Path(f"tests/fixtures/{rule_name}_bad.json"))
    schema = load_json(Path("tests/fixtures/rule_document_schema.json"))
    raw_html = load_text(Path(f"tests/fixtures/{rule_name}_raw.html"))
    return review_rule(rule, schema, raw_html)


def test_rule8_regressions():
    report = _review("rule8")
    categories = {issue.category for issue in report.confirmed_issues}
    titles = {issue.title for issue in report.confirmed_issues}
    assert report.overall_verdict.status == "not_production_ready"
    assert "amendment_markers" in categories
    assert "cross_refs" in categories
    assert "clauses" in categories
    assert any("Textless structural container allowed" in fp.title for fp in report.likely_false_positives)
    assert "Duplicate cross-reference emitted for one source mention" in titles
    assert "Historical text appears truncated" in titles


def test_rule10b_regressions():
    report = _review("rule10b")
    categories = {issue.category for issue in report.confirmed_issues}
    titles = {issue.title for issue in report.confirmed_issues}
    assert report.overall_verdict.status == "not_production_ready"
    assert "structure" in categories
    assert "tables" in categories
    assert "cross_refs" in categories
    assert "Parent branch appears collapsed into first child" in titles
    assert "Numbered table column row treated as body row" in titles
    assert "Cross-reference target is under-resolved against source mention" in titles


def test_rule26_regressions():
    report = _review("rule26")
    categories = {issue.category for issue in report.confirmed_issues}
    titles = {issue.title for issue in report.confirmed_issues}
    assert report.overall_verdict.status == "not_production_ready"
    assert "amendment_markers" in categories
    assert "statuses" in categories
    assert "Amendment action does not match source footnote" in titles
    assert "Compound footnote lost one or more structured events" in titles
    assert "Notification date is extractable from footnote but missing from amendment entry" in titles
    assert "Omitted node effective_from matches omission date" in titles
