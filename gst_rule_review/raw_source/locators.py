from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Optional


LOCATOR_RE = re.compile(
    r"(?P<target>(?:proviso to )?(?:sub-rule|rule|sub-section|section|clause|sub-clause)"
    r"(?:\s*\([^)]+\)|\s+\d+[A-Z]?)?(?:\s+of\s+(?:section|rule)\s+\d+[A-Z]?)?)",
    re.IGNORECASE,
)

MARKER_RE = re.compile(r"\[(\d+|\*{3,}|\*+)\]")
DATE_RE = re.compile(r"\b(\d{1,2}\.\d{1,2}\.\d{2,4}|\d{1,2}-\d{1,2}-\d{2,4})\b")
NOTIFICATION_RE = re.compile(r"Notification\s+No\.\s*([^,.;]+)", re.IGNORECASE)


def normalize_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.;:)\]])", r"\1", text)
    text = re.sub(r"([(\[])\s+", r"\1", text)
    return text.strip()


def extract_markers(text: str) -> list[str]:
    return [match.group(1) for match in MARKER_RE.finditer(text or "")]


def extract_locator_mentions(text: str) -> list[str]:
    seen: list[str] = []
    for match in LOCATOR_RE.finditer(text or ""):
        candidate = normalize_text(match.group("target"))
        if candidate not in seen:
            seen.append(candidate)
    return seen


def looks_like_numbering_row(values: Iterable[str]) -> bool:
    cleaned = [normalize_text(value) for value in values if normalize_text(value)]
    if not cleaned:
        return False
    return all(re.fullmatch(r"\(\w+\)", value) for value in cleaned)


def extract_notification_ref(text: str) -> Optional[str]:
    match = NOTIFICATION_RE.search(text or "")
    if match:
        return normalize_text(match.group(0))
    return None


def extract_dates(text: str) -> list[str]:
    return [match.group(1) for match in DATE_RE.finditer(text or "")]
