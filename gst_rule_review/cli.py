from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from .config import ReviewConfig
from .engine.run_review import review_rule_files
from .loader import load_json
from .raw_source.fetch import fetch_source_html
from .report.report_json import render_report_json
from .report.report_markdown import render_report_markdown

app = typer.Typer(help="Review extracted GST rule JSON against CBIC source HTML and schema.")


@app.command("review")
def review_command(
    rule: Path = typer.Option(..., exists=True, help="Extracted rule JSON file"),
    schema: Path = typer.Option(..., exists=True, help="JSON Schema file"),
    raw: Optional[Path] = typer.Option(None, exists=True, help="Raw CBIC HTML file"),
    source_url: Optional[str] = typer.Option(None, help="Source URL override"),
    config: Optional[Path] = typer.Option(None, exists=True, help="Optional review config JSON"),
    out_dir: Path = typer.Option(Path("."), help="Directory for review_report.json and review_report.md"),
) -> None:
    config_model = ReviewConfig()
    if config:
        config_model = ReviewConfig.model_validate(load_json(config))
    report = review_rule_files(
        rule_path=rule,
        schema_path=schema,
        raw_path=raw,
        source_url=source_url,
        config=config_model,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "review_report.json").write_text(render_report_json(report), encoding="utf-8")
    (out_dir / "review_report.md").write_text(render_report_markdown(report), encoding="utf-8")
    typer.echo(json.dumps(report.overall_verdict.model_dump(mode="json"), ensure_ascii=False))


@app.command("fetch-raw")
def fetch_raw_command(
    source_url: str = typer.Option(..., help="CBIC source URL"),
    out: Path = typer.Option(..., help="Destination HTML file"),
) -> None:
    html = fetch_source_html(source_url)
    out.write_text(html, encoding="utf-8")
    typer.echo(str(out))


if __name__ == "__main__":
    app()
