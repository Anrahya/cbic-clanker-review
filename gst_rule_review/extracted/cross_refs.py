from __future__ import annotations

from typing import Any


def normalize_cross_ref(ref: dict[str, Any]) -> dict[str, Any]:
    return {
        "target_text": ref.get("target_text") or ref.get("text") or "",
        "target_id": ref.get("target_id"),
        "relationship": ref.get("relationship"),
    }

