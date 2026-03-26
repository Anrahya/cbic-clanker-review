from pathlib import Path

from typer.testing import CliRunner

from gst_rule_review.cli import app


def test_cli_review_writes_reports(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "review",
            "--rule",
            "tests/fixtures/rule8_bad.json",
            "--schema",
            "tests/fixtures/rule_document_schema.json",
            "--raw",
            "tests/fixtures/rule8_raw.html",
            "--out-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "review_report.json").exists()
    assert (tmp_path / "review_report.md").exists()
    assert "not_production_ready" in result.output

