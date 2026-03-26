from pathlib import Path

from gst_rule_review.raw_source.parse_html import parse_raw_html


def test_parse_html_extracts_tables_and_footnotes():
    html = Path("tests/fixtures/rule10b_raw.html").read_text(encoding="utf-8")
    source = parse_raw_html(html)
    assert source.rule_heading == "Rule 10B. Aadhaar authentication for registered persons"
    assert len(source.tables) == 1
    assert source.tables[0].caption == "Table 1 - Documents"
    assert "1" in source.marker_to_footnote
    assert source.marker_events["1"]

