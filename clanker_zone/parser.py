from __future__ import annotations

import json
import re
from typing import Any, Dict

from .models import Judgment, ProviderResponse


FENCED_JSON_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)
SEVERITY_ALIASES = {
    "low": "minor",
    "minor": "minor",
    "medium": "moderate",
    "moderate": "moderate",
    "high": "major",
    "major": "major",
    "critical": "critical",
}
LABEL_ALIASES = {
    "no issue": "no_issue",
    "no_issue": "no_issue",
    "confirmed issue": "confirmed_issue",
    "confirmed_issue": "confirmed_issue",
    "acceptable artifact": "acceptable_artifact",
    "acceptable_artifact": "acceptable_artifact",
    "needs manual review": "needs_manual_review",
    "needs_manual_review": "needs_manual_review",
    "rejected": "no_issue",
    "not an issue": "no_issue",
    "not_an_issue": "no_issue",
    "dismiss": "no_issue",
    "dismissed": "no_issue",
    "accept": "acceptable_artifact",
    "accepted": "acceptable_artifact",
    "confirmed": "confirmed_issue",
    "issue": "confirmed_issue",
    "manual review": "needs_manual_review",
    "manual_review": "needs_manual_review",
}


def _extract_json_text(text: str) -> str:
    stripped = text.strip()
    fence_match = FENCED_JSON_RE.search(stripped)
    if fence_match:
        return fence_match.group(1)
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    decoder = json.JSONDecoder()
    for index, char in enumerate(stripped):
        if char != "{":
            continue
        try:
            _, end = decoder.raw_decode(stripped[index:])
            return stripped[index : index + end]
        except json.JSONDecodeError:
            continue
    raise ValueError("No JSON object found in model response text.")


def parse_judgment_text(text: str, *, counsel_name: str, dossier_id: str) -> Judgment:
    payload: Dict[str, Any] = json.loads(_extract_json_text(text))
    payload = _normalize_payload(payload)
    payload.setdefault("counsel_name", counsel_name)
    payload.setdefault("dossier_id", dossier_id)
    return Judgment.model_validate(payload)


def parse_judgment_response(response: ProviderResponse, *, counsel_name: str, dossier_id: str) -> Judgment:
    text_parts = [block.text for block in response.blocks if block.kind == "text" and block.text]
    if not text_parts:
        raise ValueError("Provider response did not contain any text blocks.")
    return parse_judgment_text("\n".join(text_parts), counsel_name=counsel_name, dossier_id=dossier_id)


def _normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(payload)
    label = normalized.get("label")
    if label is not None:
        label_key = str(label).strip().lower().replace("-", "_")
        normalized["label"] = LABEL_ALIASES.get(label_key, label)

    severity = normalized.get("severity")
    if severity is not None:
        severity_key = str(severity).strip().lower().replace("-", "_")
        normalized["severity"] = SEVERITY_ALIASES.get(severity_key, severity)

    evidence_refs = normalized.get("evidence_refs")
    if evidence_refs in (None, ""):
        normalized["evidence_refs"] = []
    elif isinstance(evidence_refs, str):
        normalized["evidence_refs"] = [evidence_refs]

    confidence = normalized.get("confidence")
    if confidence in (None, ""):
        normalized["confidence"] = 0.5
    elif isinstance(confidence, str):
        normalized["confidence"] = float(confidence)

    if normalized.get("recommended_fix") == "":
        normalized["recommended_fix"] = None
    if normalized.get("title") == "":
        normalized["title"] = None
    if normalized.get("problem") == "":
        normalized["problem"] = None
    return normalized
