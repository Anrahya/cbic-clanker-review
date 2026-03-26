from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from .config import CouncilConfig
from .council import CouncilBuilder
from .domains.gst.corpus import discover_rule_bundles
from .domains.gst.dossiers import build_gst_dossiers
from .domains.gst.false_positive_filter import apply_gst_false_positive_filter
from .domains.gst.policy import (
    GST_CONSTITUTION,
    GST_COUNSEL_ROSTER,
    GST_DOMAIN_OVERVIEW,
    GST_OUTPUT_CONTRACT,
)
from .domains.gst.prompts import build_issue_task_prompt, build_task_prompt
from .provider.minimax import MiniMaxProvider, MiniMaxProviderConfig
from .report.persistence import write_deliberation_artifacts, write_run_artifacts
from .session import compile_plan_requests, execute_compiled_requests
from .workflow import run_issue_council

app = typer.Typer(help="Clanker Zone multi-agent council runner.")


def _select_dossiers(dossiers, target_id: Optional[str], dossier_limit: int):
    if target_id:
        filtered = [
            dossier
            for dossier in dossiers
            if dossier.target_id == target_id
            or dossier.dossier_id == target_id
            or target_id in dossier.metadata.get("target_node_ids", [])
        ]
        if not filtered:
            raise typer.BadParameter(f"No dossier found for target_id={target_id}")
        if dossier_limit <= 0:
            return filtered
        return filtered[:dossier_limit]
    if dossier_limit <= 0:
        return dossiers
    return dossiers[:dossier_limit]


@app.command("gst-plan")
def gst_plan(
    corpus: Path = typer.Option(Path("pc"), help="Corpus root"),
    rule_number: str = typer.Option(..., help="Rule number, e.g. 26"),
    out_dir: Path = typer.Option(Path("clanker_runs/plan"), help="Output directory"),
    dossier_limit: int = typer.Option(8, help="Maximum dossiers to include"),
    target_id: Optional[str] = typer.Option(None, help="Optional node id or dossier id to isolate"),
) -> None:
    bundles = discover_rule_bundles(corpus)
    bundle = next(bundle for bundle in bundles if bundle.rule_json["metadata"]["rule_number"] == rule_number)
    dossiers = _select_dossiers(build_gst_dossiers(bundle), target_id, dossier_limit)
    builder = CouncilBuilder(CouncilConfig(), "gst", GST_COUNSEL_ROSTER)
    plan = builder.build_plan(
        dossiers=dossiers,
        constitution=GST_CONSTITUTION,
        domain_overview=GST_DOMAIN_OVERVIEW,
        output_contract=GST_OUTPUT_CONTRACT,
        metadata={"rule_number": rule_number},
    )
    provider = MiniMaxProvider(MiniMaxProviderConfig())
    compiled = compile_plan_requests(plan=plan, provider=provider, prompt_builder=build_task_prompt)
    write_run_artifacts(out_dir=out_dir, plan=plan, compiled_requests=compiled)
    typer.echo(str(out_dir))


@app.command("gst-run")
def gst_run(
    corpus: Path = typer.Option(Path("pc"), help="Corpus root"),
    rule_number: str = typer.Option(..., help="Rule number, e.g. 26"),
    out_dir: Path = typer.Option(Path("clanker_runs/live"), help="Output directory"),
    dossier_limit: int = typer.Option(4, help="Maximum dossiers to execute live"),
    model: str = typer.Option("MiniMax-M2.7", help="MiniMax model name"),
    target_id: Optional[str] = typer.Option(None, help="Optional node id or dossier id to isolate"),
    counsel_name: Optional[str] = typer.Option(None, help="Optional counsel name to isolate"),
    max_tokens: int = typer.Option(4096, help="Max output tokens per MiniMax request"),
    timeout_seconds: float = typer.Option(180.0, help="HTTP timeout per MiniMax request"),
    max_retries: int = typer.Option(3, help="Retry count for transient MiniMax network timeouts"),
) -> None:
    bundles = discover_rule_bundles(corpus)
    bundle = next(bundle for bundle in bundles if bundle.rule_json["metadata"]["rule_number"] == rule_number)
    dossiers = _select_dossiers(build_gst_dossiers(bundle), target_id, dossier_limit)
    builder = CouncilBuilder(CouncilConfig(model_name=model), "gst", GST_COUNSEL_ROSTER)
    plan = builder.build_plan(
        dossiers=dossiers,
        constitution=GST_CONSTITUTION,
        domain_overview=GST_DOMAIN_OVERVIEW,
        output_contract=GST_OUTPUT_CONTRACT,
        metadata={"rule_number": rule_number},
    )
    provider = MiniMaxProvider(
        MiniMaxProviderConfig(
            model=model,
            max_tokens=max_tokens,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )
    )
    compiled = compile_plan_requests(plan=plan, provider=provider, prompt_builder=build_task_prompt)
    live_compiled = [item for item in compiled if item.stage != "docket"]
    if counsel_name:
        live_compiled = [item for item in live_compiled if item.counsel_name == counsel_name]
        if not live_compiled:
            raise typer.BadParameter(f"No live tasks found for counsel_name={counsel_name}")
    executed = execute_compiled_requests(compiled_requests=live_compiled, provider=provider)
    write_run_artifacts(out_dir=out_dir, plan=plan, compiled_requests=compiled, executed_results=executed)
    typer.echo(str(out_dir))


@app.command("gst-review")
def gst_review(
    corpus: Path = typer.Option(Path("pc"), help="Corpus root"),
    rule_number: str = typer.Option(..., help="Rule number, e.g. 26"),
    out_dir: Path = typer.Option(Path("clanker_runs/review"), help="Output directory"),
    dossier_limit: int = typer.Option(0, help="Maximum dossiers to execute live; 0 means all dossiers"),
    model: str = typer.Option("MiniMax-M2.7", help="MiniMax model name"),
    target_id: Optional[str] = typer.Option(None, help="Optional node id or dossier id to isolate"),
    specialist_counsel: Optional[str] = typer.Option(
        None,
        help="Optional comma-separated specialist counsel names to isolate, e.g. amendment_counsel,reference_counsel",
    ),
    max_tokens: int = typer.Option(4096, help="Max output tokens per MiniMax request"),
    timeout_seconds: float = typer.Option(180.0, help="HTTP timeout per MiniMax request"),
    max_retries: int = typer.Option(3, help="Retry count for transient MiniMax network timeouts"),
    max_concurrency: int = typer.Option(6, help="Maximum parallel MiniMax requests per stage"),
) -> None:
    bundles = discover_rule_bundles(corpus)
    bundle = next(bundle for bundle in bundles if bundle.rule_json["metadata"]["rule_number"] == rule_number)
    dossiers = _select_dossiers(build_gst_dossiers(bundle), target_id, dossier_limit)
    builder = CouncilBuilder(CouncilConfig(model_name=model), "gst", GST_COUNSEL_ROSTER)
    plan = builder.build_plan(
        dossiers=dossiers,
        constitution=GST_CONSTITUTION,
        domain_overview=GST_DOMAIN_OVERVIEW,
        output_contract=GST_OUTPUT_CONTRACT,
        metadata={"rule_number": rule_number},
    )
    provider = MiniMaxProvider(
        MiniMaxProviderConfig(
            model=model,
            max_tokens=max_tokens,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )
    )
    specialist_names = None
    if specialist_counsel:
        specialist_names = [item.strip() for item in specialist_counsel.split(",") if item.strip()]
    run = run_issue_council(
        plan=plan,
        roster=GST_COUNSEL_ROSTER,
        provider=provider,
        specialist_prompt_builder=build_task_prompt,
        issue_prompt_builder=build_issue_task_prompt,
        specialist_counsel_names=specialist_names,
        max_concurrency=max_concurrency,
    )
    run.rule_report = apply_gst_false_positive_filter(
        report=run.rule_report,
        dossiers=plan.dossiers,
    )
    write_deliberation_artifacts(out_dir=out_dir, plan=plan, run=run)
    typer.echo(str(out_dir))


if __name__ == "__main__":
    app()
