from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional

from bs4 import BeautifulSoup
from lxml import html
from lxml import etree

from ..models import RawSourceModel, SourceBlock
from .footnotes import extract_footnote_events, is_footnote_text
from .locators import extract_markers, normalize_text
from .tables import parse_table


TEXT_TAGS = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "caption"}
CONTAINER_TAGS = {"div"}


def _dom_path(element: etree._Element) -> str:
    parts: list[str] = []
    current = element
    while current is not None and isinstance(current.tag, str):
        parent = current.getparent()
        if parent is None:
            parts.append(current.tag)
            break
        siblings = [sib for sib in parent if sib.tag == current.tag]
        index = siblings.index(current) + 1 if current in siblings else 1
        parts.append(f"{current.tag}[{index}]")
        current = parent
    return "/" + "/".join(reversed(parts))


def _should_emit_div(element: etree._Element) -> bool:
    child_tags = {child.tag.lower() for child in element if isinstance(child.tag, str)}
    return not child_tags.intersection(TEXT_TAGS | {"table"} | CONTAINER_TAGS)


def parse_raw_html(raw_html: str, source_url: Optional[str] = None) -> RawSourceModel:
    BeautifulSoup(raw_html, "lxml")
    document = html.fromstring(raw_html)
    body = document.find(".//body")
    if body is None:
        body = document
    blocks: List[SourceBlock] = []
    tables = []
    footnotes = []
    marker_to_footnote: Dict[str, int] = {}
    marker_events = defaultdict(list)
    block_id = 1

    for element in body.iter():
        if not isinstance(element.tag, str):
            continue
        tag = element.tag.lower()
        if tag == "script" or tag == "style":
            continue
        if tag == "table":
            table = parse_table(element, block_id)
            table_text = "\n".join(
                " | ".join(cell.text for cell in row.cells if cell.text) for row in table.rows if row.cells
            )
            block = SourceBlock(
                block_id=block_id,
                kind="table",
                text=table_text,
                normalized_text=normalize_text(table_text),
                line_number=element.sourceline,
                dom_path=_dom_path(element),
                markers=[],
                metadata={"caption": table.caption},
            )
            blocks.append(block)
            tables.append(table)
            block_id += 1
            continue
        if tag not in TEXT_TAGS and not (tag in CONTAINER_TAGS and _should_emit_div(element)):
            continue
        text = normalize_text(" ".join(element.itertext()))
        if not text:
            continue
        parent = element.getparent()
        if parent is not None and isinstance(parent.tag, str):
            parent_tag = parent.tag.lower()
            if tag in TEXT_TAGS and parent_tag in TEXT_TAGS | CONTAINER_TAGS:
                continue
        kind = "heading" if tag.startswith("h") else "caption" if tag == "caption" else "text"
        if is_footnote_text(text):
            kind = "footnote"
        block = SourceBlock(
            block_id=block_id,
            kind=kind,
            text=text,
            normalized_text=normalize_text(text),
            line_number=element.sourceline,
            dom_path=_dom_path(element),
            markers=extract_markers(text),
            metadata={},
        )
        blocks.append(block)
        if kind == "footnote":
            footnotes.append(block)
            if block.markers:
                marker_to_footnote[block.markers[0]] = block.block_id
            for event in extract_footnote_events(block):
                marker_events[event.marker].append(event)
        block_id += 1

    heading = next((block.text for block in blocks if block.kind == "heading"), None)
    return RawSourceModel(
        source_url=source_url,
        rule_heading=heading,
        blocks=blocks,
        tables=tables,
        footnotes=footnotes,
        marker_to_footnote=marker_to_footnote,
        marker_events=dict(marker_events),
    )
