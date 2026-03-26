from __future__ import annotations

import re

from ..models import FootnoteEvent, SourceBlock
from .locators import extract_dates, extract_markers, extract_notification_ref, normalize_text


ACTION_MAP = {
    "inserted": "INSERTED",
    "substituted": "SUBSTITUTED",
    "omitted": "OMITTED",
    "inserted vide": "INSERTED",
    "substituted vide": "SUBSTITUTED",
    "omitted vide": "OMITTED",
    "enforced": "ENFORCED",
    "came into force": "ENFORCED",
}


def is_footnote_text(text: str) -> bool:
    normalized = normalize_text(text)
    return bool(re.match(r"^\[(\d+|\*+)\]", normalized)) or "vide Notification No." in normalized


def extract_footnote_events(block: SourceBlock) -> list[FootnoteEvent]:
    text = block.text
    markers = extract_markers(text)
    if not markers:
        return []

    marker = markers[0]
    fragments = re.split(r";|\.\s+(?=[A-Z])", text)
    events: list[FootnoteEvent] = []
    for fragment in fragments:
        normalized = normalize_text(fragment)
        lower = normalized.lower()
        action = None
        for token, mapped in ACTION_MAP.items():
            if token in lower:
                action = mapped
                break
        if "w.e.f" in lower or "with effect from" in lower:
            events.append(
                FootnoteEvent(
                    marker=marker,
                    action="ENFORCED",
                    notification_ref=extract_notification_ref(normalized),
                    notification_date=extract_dates(normalized)[0] if extract_dates(normalized) else None,
                    effective_date=extract_dates(normalized)[-1] if extract_dates(normalized) else None,
                    text_fragment=normalized,
                )
            )
        if action:
            dates = extract_dates(normalized)
            events.append(
                FootnoteEvent(
                    marker=marker,
                    action=action,
                    notification_ref=extract_notification_ref(normalized),
                    notification_date=dates[0] if dates else None,
                    effective_date=dates[-1] if dates else None,
                    text_fragment=normalized,
                )
            )
    return events

