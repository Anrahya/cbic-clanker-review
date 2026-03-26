from __future__ import annotations

from jsonschema import Draft202012Validator

from .models import SchemaErrorDetail, SchemaValidationResult


def _path_to_json_path(path: list[object]) -> str:
    if not path:
        return "$"
    parts = ["$"]
    for item in path:
        if isinstance(item, int):
            parts.append(f"[{item}]")
        else:
            parts.append(f".{item}")
    return "".join(parts)


def validate_rule_json(rule_json: dict, schema_json: dict) -> SchemaValidationResult:
    validator = Draft202012Validator(schema_json)
    errors = sorted(validator.iter_errors(rule_json), key=lambda err: list(err.path))
    details = [
        SchemaErrorDetail(
            message=error.message,
            json_path=_path_to_json_path(list(error.absolute_path)),
            validator=error.validator,
        )
        for error in errors
    ]
    blocking = False
    if details:
        root_failures = {detail.json_path for detail in details if detail.json_path == "$"}
        blocking = bool(root_failures)
    return SchemaValidationResult(valid=not details, blocking=blocking, errors=details)

