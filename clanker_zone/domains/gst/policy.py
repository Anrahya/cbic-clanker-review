from __future__ import annotations

from ...models import CounselSpec


GST_REVIEW_CATEGORIES = [
    "text_fidelity",
    "raw_text_traceability",
    "structure_scope",
    "clauses",
    "provisos_explanations",
    "tables",
    "formulas",
    "amendment_markers",
    "source_refs",
    "cross_refs",
    "status_chronology",
    "duplicates",
]

GST_CONSTITUTION = """
You are part of Clanker Zone, a strict evidence-first review council.
Review only real defects.
Do not punish harmless CBIC formatting artifacts.
Treat hint-derived source blocks and raw HTML as provenance evidence.
Every confirmed issue must cite exact evidence and explain why it is a real defect.
If uncertain, return needs_manual_review instead of over-asserting.
"""

GST_DOMAIN_OVERVIEW = """
Domain: GST rule extraction review.
Primary evidence hierarchy:
1. raw source meaning
2. hint-derived structured evidence
3. schema semantics
4. extracted rule JSON
Known source quirks:
- amendment markers can span multiple blocks and provisos
- CBIC spacing and punctuation are often ugly but legally harmless
- numbered table rows like (1) and (2) may still be header structure
- source_ref.anchor_text is a short UI anchor phrase, not a verbatim exact quote
- display_label may legitimately hold the clause/proviso label while text omits it
- raw_text may legitimately be null when source_ref is the authoritative audit anchor
- cross_ref.target_id may legitimately be null when deterministic resolution is unavailable
- effective_until on an omitted node can be valid chronology, not duplicate status
- enacted_date alone does not prove effective_from
Known non-issues unless stronger source evidence proves otherwise:
- anchor_text being shorter than the full source block
- anchor_text omitting a clause label like (b), (e), or (h)
- separate sibling nodes each carrying the same cross_ref when the source repeats the mention separately
- missing target_id for external_act references
- text omitting a legal label that is already preserved in display_label
"""

GST_OUTPUT_CONTRACT = """
Return only one of:
- confirmed_issue
- acceptable_artifact
- needs_manual_review
- no_issue
Return JSON only with this shape:
{
  "label": "...",
  "category": "...",
  "node_id": "...",
  "severity": "...",
  "title": "...",
  "problem": "...",
  "evidence_refs": ["..."],
  "recommended_fix": "...",
  "confidence": 0.0
}
The dossier may cover a whole sub-rule or clause cluster.
When you return a finding, node_id must point to the exact affected node from the dossier's target cards, not just the cluster root.
Severity must be exactly one of: critical, major, moderate, minor.
Use [] for evidence_refs when there is no concrete citation.
Use a numeric confidence. If uncertain, use 0.5 and downgrade the label instead of inventing certainty.
Use null where a field does not apply. Do not emit markdown.
"""

GST_COUNSEL_ROSTER = [
    CounselSpec(
        name="source_fidelity_counsel",
        stage="specialist",
        categories=["text_fidelity", "raw_text_traceability"],
        prompt_key="gst.source_fidelity",
    ),
    CounselSpec(
        name="structure_scope_counsel",
        stage="specialist",
        categories=["structure_scope", "clauses", "provisos_explanations"],
        prompt_key="gst.structure_scope",
    ),
    CounselSpec(
        name="amendment_counsel",
        stage="specialist",
        categories=["amendment_markers", "status_chronology"],
        prompt_key="gst.amendment",
    ),
    CounselSpec(
        name="reference_counsel",
        stage="specialist",
        categories=["source_refs", "cross_refs", "duplicates"],
        prompt_key="gst.references",
    ),
    CounselSpec(
        name="table_counsel",
        stage="specialist",
        categories=["tables"],
        prompt_key="gst.tables",
    ),
    CounselSpec(
        name="artifact_defender",
        stage="skeptic",
        categories=GST_REVIEW_CATEGORIES,
        prompt_key="gst.artifact_defender",
    ),
    CounselSpec(
        name="chief_arbiter",
        stage="arbiter",
        categories=GST_REVIEW_CATEGORIES,
        prompt_key="gst.arbiter",
    ),
]
