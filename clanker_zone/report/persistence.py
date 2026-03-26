from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from ..models import CompiledTaskRequest, CouncilDeliberationRun, CouncilRunPlan, ExecutedTaskResult


def write_run_artifacts(
    *,
    out_dir: Path,
    plan: CouncilRunPlan,
    compiled_requests: List[CompiledTaskRequest],
    executed_results: Optional[List[ExecutedTaskResult]] = None,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "plan.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")
    (out_dir / "compiled_requests.json").write_text(
        json.dumps([item.model_dump(mode="json") for item in compiled_requests], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if executed_results is not None:
        (out_dir / "executed_results.json").write_text(
            json.dumps([item.model_dump(mode="json") for item in executed_results], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def write_deliberation_artifacts(
    *,
    out_dir: Path,
    plan: CouncilRunPlan,
    run: CouncilDeliberationRun,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "plan.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")
    (out_dir / "specialist_compiled_requests.json").write_text(
        json.dumps([item.model_dump(mode="json") for item in run.specialist_compiled_requests], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "specialist_results.json").write_text(
        json.dumps([item.model_dump(mode="json") for item in run.specialist_results], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "candidate_issues.json").write_text(
        json.dumps([item.model_dump(mode="json") for item in run.candidate_issues], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "challenge_compiled_requests.json").write_text(
        json.dumps([item.model_dump(mode="json") for item in run.challenge_compiled_requests], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "challenge_results.json").write_text(
        json.dumps([item.model_dump(mode="json") for item in run.challenge_results], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "arbiter_compiled_requests.json").write_text(
        json.dumps([item.model_dump(mode="json") for item in run.arbiter_compiled_requests], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "arbiter_results.json").write_text(
        json.dumps([item.model_dump(mode="json") for item in run.arbiter_results], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "rule_report.json").write_text(run.rule_report.model_dump_json(indent=2), encoding="utf-8")
