from __future__ import annotations

from ..models import OverallVerdict, SchemaValidationResult
from .severity import severity_counts


def determine_verdict(schema_validation: SchemaValidationResult, confirmed_issue_count: int, findings: list) -> OverallVerdict:
    if schema_validation.blocking:
        return OverallVerdict(
            status="schema_invalid",
            summary="Schema validation failed at the document root, which blocks a meaningful review.",
        )
    if confirmed_issue_count == 0:
        return OverallVerdict(
            status="production_ready",
            summary="No confirmed extraction defects were found against the schema and mapped source evidence.",
        )
    counts = severity_counts(findings)
    if counts.get("critical", 0) or counts.get("major", 0):
        return OverallVerdict(
            status="not_production_ready",
            summary="At least one confirmed major or critical defect materially affects legal meaning, structure, or provenance.",
        )
    return OverallVerdict(
        status="close_but_not_ready",
        summary="Only moderate/minor confirmed issues were found, but the extraction still needs correction before production use.",
    )

