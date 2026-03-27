from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..checks import (
    amendment_markers,
    chronology,
    clauses,
    cross_refs,
    duplicates,
    formulas,
    provisos_explanations,
    raw_text,
    source_refs,
    statuses,
    structure,
    tables,
    text_fidelity,
)
from ..config import ReviewConfig
from ..extracted.node_index import index_rule_json
from ..loader import load_json, resolve_hint_json, resolve_raw_html
from ..models import CheckContext, InputSummary, ReviewReport
from ..raw_source.parse_html import parse_raw_html
from ..schema_validate import validate_rule_json
from .false_positive_filter import filter_findings
from .verdict import determine_verdict


CHECKS = [
    text_fidelity.run,
    raw_text.run,
    structure.run,
    provisos_explanations.run,
    clauses.run,
    formulas.run,
    tables.run,
    amendment_markers.run,
    source_refs.run,
    cross_refs.run,
    statuses.run,
    chronology.run,
    duplicates.run,
]


def review_rule(
    rule_json: Dict[str, Any],
    schema_json: Dict[str, Any],
    raw_html: str,
    *,
    source_url: Optional[str] = None,
    config: Optional[ReviewConfig] = None,
    rule_path: Optional[str] = None,
    schema_path: Optional[str] = None,
    raw_path: Optional[str] = None,
    hint_json: Optional[Dict[str, Any]] = None,
) -> ReviewReport:
    config = config or ReviewConfig()
    schema_validation = validate_rule_json(rule_json, schema_json)
    indexed_rule = index_rule_json(rule_json)
    raw_source = parse_raw_html(raw_html, source_url=source_url)
    context = CheckContext(
        config=config,
        rule_json=rule_json,
        rule_schema=schema_json,
        raw_source=raw_source,
        indexed_rule=indexed_rule,
        schema_validation=schema_validation,
        hint_json=hint_json or {},
    )
    findings = []
    likely_false_positives = []
    for check in CHECKS:
        result = check(context)
        findings.extend(result.findings)
        likely_false_positives.extend(result.likely_false_positives)
    findings, likely_false_positives = filter_findings(
        findings=findings,
        likely_false_positives=likely_false_positives,
        tolerate_spacing_artifacts=config.tolerate_cbic_spacing_artifacts,
        min_confirm_confidence=config.min_confirm_confidence,
    )
    verdict = determine_verdict(schema_validation, len(findings), findings)
    return ReviewReport(
        input_summary=InputSummary(
            rule_path=rule_path,
            schema_path=schema_path,
            raw_path=raw_path,
            source_url=source_url,
            rule_id=next(iter(indexed_rule.nodes.values())).node_id if indexed_rule.nodes else None,
            node_count=len(indexed_rule.nodes),
            raw_block_count=len(raw_source.blocks),
            table_count=len(raw_source.tables),
        ),
        schema_validation=schema_validation,
        confirmed_issues=findings,
        likely_false_positives=likely_false_positives,
        overall_verdict=verdict,
    )


def review_rule_files(
    *,
    rule_path: Union[str, Path],
    schema_path: Union[str, Path],
    raw_path: Optional[Union[str, Path]] = None,
    source_url: Optional[str] = None,
    config: Optional[ReviewConfig] = None,
    hint_json: Optional[Dict[str, Any]] = None,
) -> ReviewReport:
    rule_json = load_json(rule_path)
    schema_json = load_json(schema_path)
    raw_html, resolved_raw_path = resolve_raw_html(raw_path, source_url, rule_json.get("metadata"))
    # Auto-resolve hint JSON if not explicitly provided
    if hint_json is None:
        hint_json = resolve_hint_json(rule_json, resolved_raw_path)
    return review_rule(
        rule_json,
        schema_json,
        raw_html,
        source_url=source_url or rule_json.get("metadata", {}).get("source_url"),
        config=config,
        rule_path=str(rule_path),
        schema_path=str(schema_path),
        raw_path=resolved_raw_path,
        hint_json=hint_json,
    )
