from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


Severity = Literal["critical", "major", "moderate", "minor"]
VerdictStatus = Literal[
    "production_ready",
    "close_but_not_ready",
    "not_production_ready",
    "schema_invalid",
]


class SourceLocator(BaseModel):
    block_ids: List[int] = Field(default_factory=list)
    line_hint: Optional[str] = None
    dom_path: Optional[str] = None


class Finding(BaseModel):
    issue_id: str
    node_id: Optional[str] = None
    json_path: Optional[str] = None
    category: str
    severity: Severity
    title: str
    problem: str
    raw_source_fragment: Optional[str] = None
    source_locator: SourceLocator = Field(default_factory=SourceLocator)
    json_fragment: Any = None
    why_real_defect: str
    recommended_fix: str
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class LikelyFalsePositive(BaseModel):
    title: str
    reason: str
    raw_source_fragment: Optional[str] = None
    json_fragment: Any = None


class SchemaErrorDetail(BaseModel):
    message: str
    json_path: str
    validator: Optional[str] = None


class SchemaValidationResult(BaseModel):
    valid: bool = True
    blocking: bool = False
    errors: List[SchemaErrorDetail] = Field(default_factory=list)


class OverallVerdict(BaseModel):
    status: VerdictStatus
    summary: str


class InputSummary(BaseModel):
    rule_path: Optional[str] = None
    schema_path: Optional[str] = None
    raw_path: Optional[str] = None
    source_url: Optional[str] = None
    rule_id: Optional[str] = None
    node_count: int = 0
    raw_block_count: int = 0
    table_count: int = 0


class ReviewReport(BaseModel):
    input_summary: InputSummary
    schema_validation: SchemaValidationResult
    confirmed_issues: List[Finding] = Field(default_factory=list)
    likely_false_positives: List[LikelyFalsePositive] = Field(default_factory=list)
    overall_verdict: OverallVerdict


class SourceBlock(BaseModel):
    block_id: int
    kind: Literal["heading", "text", "table", "caption", "footnote"]
    text: str
    normalized_text: str
    line_number: Optional[int] = None
    dom_path: Optional[str] = None
    markers: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SourceTableCell(BaseModel):
    text: str
    colspan: int = 1
    rowspan: int = 1


class SourceTableRow(BaseModel):
    cells: List[SourceTableCell] = Field(default_factory=list)
    is_header: bool = False
    is_numbering_row: bool = False


class SourceTable(BaseModel):
    block_id: int
    caption: Optional[str] = None
    rows: List[SourceTableRow] = Field(default_factory=list)


class FootnoteEvent(BaseModel):
    marker: str
    action: str
    notification_ref: Optional[str] = None
    notification_date: Optional[str] = None
    effective_date: Optional[str] = None
    text_fragment: str


class RawSourceModel(BaseModel):
    source_url: Optional[str] = None
    rule_heading: Optional[str] = None
    rule_number: Optional[str] = None
    title: Optional[str] = None
    blocks: List[SourceBlock] = Field(default_factory=list)
    tables: List[SourceTable] = Field(default_factory=list)
    footnotes: List[SourceBlock] = Field(default_factory=list)
    marker_to_footnote: Dict[str, int] = Field(default_factory=dict)
    marker_events: Dict[str, List[FootnoteEvent]] = Field(default_factory=dict)


class IndexedNode(BaseModel):
    node_id: str
    json_path: str
    node_type: str
    parent_id: Optional[str] = None
    label: Optional[str] = None
    display_label: Optional[str] = None
    text: Optional[str] = None
    operative_text: Optional[str] = None
    raw_text: Optional[str] = None
    status: Optional[str] = None
    source_ref: Any = None
    amendment_markers: List[str] = Field(default_factory=list)
    cross_refs: List[Dict[str, Any]] = Field(default_factory=list)
    effective_from: Optional[str] = None
    effective_until: Optional[str] = None
    node: Dict[str, Any] = Field(default_factory=dict)


class IndexedRule(BaseModel):
    rule_json: Dict[str, Any]
    root_node_id: Optional[str] = None
    nodes: Dict[str, IndexedNode] = Field(default_factory=dict)
    parent_map: Dict[str, Optional[str]] = Field(default_factory=dict)
    children_map: Dict[str, List[str]] = Field(default_factory=dict)
    path_index: Dict[str, str] = Field(default_factory=dict)
    label_index: Dict[str, str] = Field(default_factory=dict)
    type_index: Dict[str, List[str]] = Field(default_factory=dict)
    marker_to_nodes: Dict[str, List[str]] = Field(default_factory=dict)
    source_block_coverage: Dict[str, List[int]] = Field(default_factory=dict)
    amendment_map: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class CheckContext(BaseModel):
    config: Any
    rule_json: Dict[str, Any]
    rule_schema: Dict[str, Any]
    raw_source: RawSourceModel
    indexed_rule: IndexedRule
    schema_validation: SchemaValidationResult


class CheckResult(BaseModel):
    findings: List[Finding] = Field(default_factory=list)
    likely_false_positives: List[LikelyFalsePositive] = Field(default_factory=list)
