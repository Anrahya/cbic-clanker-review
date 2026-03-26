import pytest

from clanker_zone.parser import parse_judgment_text


def test_parse_judgment_text_from_plain_json():
    judgment = parse_judgment_text(
        '{"label":"no_issue","category":null,"confidence":0.82}',
        counsel_name="demo_counsel",
        dossier_id="d1",
    )
    assert judgment.label == "no_issue"
    assert judgment.counsel_name == "demo_counsel"
    assert judgment.dossier_id == "d1"


def test_parse_judgment_text_from_fenced_json():
    judgment = parse_judgment_text(
        '```json\n{"label":"acceptable_artifact","category":"text_fidelity","confidence":0.7}\n```',
        counsel_name="demo_counsel",
        dossier_id="d2",
    )
    assert judgment.label == "acceptable_artifact"
    assert judgment.category == "text_fidelity"


def test_parse_judgment_text_raises_when_missing_json():
    with pytest.raises(ValueError):
        parse_judgment_text("not json", counsel_name="demo_counsel", dossier_id="d3")


def test_parse_judgment_text_normalizes_common_minimax_drift():
    judgment = parse_judgment_text(
        '{"label":"confirmed_issue","category":"cross_refs","severity":"medium","evidence_refs":null,"confidence":null}',
        counsel_name="demo_counsel",
        dossier_id="d4",
    )
    assert judgment.label == "confirmed_issue"
    assert judgment.severity == "moderate"
    assert judgment.evidence_refs == []
    assert judgment.confidence == 0.5
