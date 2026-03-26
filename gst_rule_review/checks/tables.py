from __future__ import annotations

from .common import build_finding
from ..models import CheckContext, CheckResult
from ..raw_source.locators import looks_like_numbering_row, normalize_text


def _node_headers(node: dict) -> list[list[str]]:
    headers = node.get("headers") or []
    return [[normalize_text(str(cell)) for cell in row] for row in headers]


def _node_rows(node: dict) -> list[list[str]]:
    rows = node.get("rows") or []
    return [[normalize_text(str(cell)) for cell in row] for row in rows]


def run(context: CheckContext) -> CheckResult:
    result = CheckResult()
    source_tables = {table.block_id: table for table in context.raw_source.tables}
    for node in context.indexed_rule.nodes.values():
        if node.node_type.lower() != "table":
            continue
        source_ref = node.source_ref or {}
        block_ids = source_ref.get("block_ids") or source_ref.get("blocks") or []
        table = next((source_tables.get(int(block_id)) for block_id in block_ids if int(block_id) in source_tables), None)
        if not table:
            continue
        headers = _node_headers(node.node)
        rows = _node_rows(node.node)
        if table.caption and normalize_text(node.node.get("caption", "")) != normalize_text(table.caption):
            result.findings.append(
                build_finding(
                    issue_id=f"TABLE-CAPTION-{node.node_id}",
                    category="tables",
                    severity="moderate",
                    title="Table caption does not match mapped source table",
                    problem="The extracted table caption differs from the source caption.",
                    node=node,
                    raw_source_fragment=table.caption,
                    why_real_defect="Caption mismatches can attach the wrong explanatory text to the table.",
                    recommended_fix="Copy the caption directly from the mapped source table.",
                    confidence=0.87,
                )
            )
        source_row_texts = [[normalize_text(cell.text) for cell in row.cells] for row in table.rows]
        numbering_row = next((row for row in source_row_texts if looks_like_numbering_row(row)), None)
        if numbering_row and rows and rows[0] == numbering_row and numbering_row not in headers:
            result.findings.append(
                build_finding(
                    issue_id=f"TABLE-HEADER-{node.node_id}",
                    category="tables",
                    severity="major",
                    title="Numbered table column row treated as body row",
                    problem="A source numbering row like (1), (2) has been emitted as table body content instead of header metadata.",
                    node=node,
                    raw_source_fragment=" | ".join(numbering_row),
                    why_real_defect="This changes the semantics of the source table structure and breaks alignment with the source columns.",
                    recommended_fix="Classify the numbering row as part of the table header structure rather than as a body row.",
                    confidence=0.96,
                )
            )
        if rows and len(rows) != max(len(source_row_texts) - len(headers), 0):
            result.findings.append(
                build_finding(
                    issue_id=f"TABLE-SHAPE-{node.node_id}",
                    category="tables",
                    severity="moderate",
                    title="Extracted table row count does not match source table",
                    problem="The extracted table body shape differs from the mapped source table.",
                    node=node,
                    raw_source_fragment="\n".join(" | ".join(row) for row in source_row_texts),
                    why_real_defect="Row misalignment can shift values across columns and change meaning.",
                    recommended_fix="Rebuild the table rows from the source HTML table preserving header/body boundaries and order.",
                    confidence=0.79,
                )
            )
    return result

