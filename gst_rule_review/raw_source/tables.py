from __future__ import annotations

from lxml import etree

from ..models import SourceTable, SourceTableCell, SourceTableRow
from .locators import looks_like_numbering_row, normalize_text


def parse_table(table_el: etree._Element, block_id: int) -> SourceTable:
    caption = None
    caption_el = table_el.find(".//caption")
    if caption_el is not None:
        caption = normalize_text(" ".join(caption_el.itertext()))

    rows: list[SourceTableRow] = []
    for tr in table_el.xpath(".//tr"):
        cell_els = tr.xpath("./th|./td")
        cells = [
            SourceTableCell(
                text=normalize_text(" ".join(cell.itertext())),
                colspan=int(cell.attrib.get("colspan", "1") or "1"),
                rowspan=int(cell.attrib.get("rowspan", "1") or "1"),
            )
            for cell in cell_els
        ]
        texts = [cell.text for cell in cells]
        rows.append(
            SourceTableRow(
                cells=cells,
                is_header=bool(cell_els and all(cell.tag.lower() == "th" for cell in cell_els)),
                is_numbering_row=looks_like_numbering_row(texts),
            )
        )
    return SourceTable(block_id=block_id, caption=caption, rows=rows)

