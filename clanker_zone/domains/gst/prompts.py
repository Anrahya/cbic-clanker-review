from __future__ import annotations

import json
from typing import Dict, List

from ...models import CandidateIssue, Dossier, Judgment
from .policy import GST_CONSTITUTION, GST_DOMAIN_OVERVIEW, GST_OUTPUT_CONTRACT


GST_PROMPT_REGISTRY: Dict[str, str] = {
    "core.docket": """
You are the docket clerk.
Do not judge the dossier.
Summarize the evidence scope, likely review angles, and missing context risks.
""".strip(),
    "gst.source_fidelity": """
You are source_fidelity_counsel.
Review only text fidelity and raw text provenance.
Do not comment on tables, chronology, or cross-reference ontology unless it directly affects text fidelity.
Do not treat a short source_ref.anchor_text preview as truncated legal text.
Do not require text to repeat a clause/proviso label when display_label already preserves it.
Do not require raw_text when source_ref already provides the audit anchor.
""".strip(),
    "gst.structure_scope": """
You are structure_scope_counsel.
Review only structure, clause splitting, proviso/explanation attachment, and scope.
Treat source-faithful multi-block bracket spans as acceptable unless they misstate node scope.
Do not flag a node merely because text omits a leading label like (b) when display_label already carries it.
""".strip(),
    "gst.amendment": """
You are amendment_counsel.
Review only amendment markers, footnotes, action types, and chronology/status fields.
Be strict about marker scope and compound footnote event loss.
Do not flag effective_until on an omitted node as redundant by itself.
Do not infer effective_from from enacted_date alone unless the source explicitly makes that date operative.
""".strip(),
    "gst.references": """
You are reference_counsel.
Review only source_ref precision, cross_refs, target granularity, and duplicate references.
Preserve the most specific target text visible in the source.
Do not require target_id when the schema allows null and deterministic resolution is unavailable.
Do not treat anchor_text as a verbatim quote requirement.
Do not call repeated cross_refs across different sibling nodes duplicates when the source repeats the citation separately in each sibling.
""".strip(),
    "gst.tables": """
You are table_counsel.
Review only table structure, captions, header/body semantics, numbering rows, and row/column meaning.
""".strip(),
    "gst.artifact_defender": """
You are artifact_defender.
Assume a claimed issue may be a harmless CBIC source artifact.
Argue against over-flagging and downgrade borderline cases to acceptable_artifact or needs_manual_review.
""".strip(),
    "gst.challenge_issue": """
You are artifact_defender.
Review one candidate issue, not the whole dossier.
Assume the proposing specialist may be wrong or over-reading a harmless CBIC artifact.
Reject or downgrade the candidate issue unless the cited evidence clearly supports it.
Actively reject issues that depend only on short anchor_text previews, optional target_id values, or display_label/text separation.
""".strip(),
    "gst.arbiter": """
You are chief_arbiter.
Review the dossier conservatively and decide only what can be confirmed from the evidence.
Do not invent issues to fill coverage gaps.
""".strip(),
    "gst.arbitrate_issue": """
You are chief_arbiter.
Review one candidate issue together with the prior specialist and skeptic judgments.
Confirm only issues that survive challenge and remain supported by exact evidence.
If the issue depends only on anchor_text preview length, optional target_id, or whether text repeats display_label, do not confirm it.
""".strip(),
}


def get_shared_prefix() -> str:
    return "\n\n".join([GST_CONSTITUTION.strip(), GST_DOMAIN_OVERVIEW.strip(), GST_OUTPUT_CONTRACT.strip()])


def build_task_prompt(prompt_key: str, dossier: Dossier, categories: List[str]) -> str:
    instruction = GST_PROMPT_REGISTRY[prompt_key]
    evidence_blocks = _serialize_evidence(dossier)
    payload = {
        "instruction": instruction,
        "dossier": {
            "dossier_id": dossier.dossier_id,
            "kind": dossier.kind,
            "target_id": dossier.target_id,
            "title": dossier.title,
            "category_focus": categories,
            "candidate_fragment": dossier.candidate_fragment,
            "schema_excerpt": dossier.schema_excerpt,
            "evidence": evidence_blocks,
            "metadata": dossier.metadata,
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_issue_task_prompt(
    prompt_key: str,
    dossier: Dossier,
    issue: CandidateIssue,
    prior_judgments: List[Judgment],
) -> str:
    instruction = GST_PROMPT_REGISTRY[prompt_key]
    payload = {
        "instruction": instruction,
        "candidate_issue": issue.model_dump(mode="json"),
        "prior_judgments": [_serialize_judgment(judgment) for judgment in prior_judgments],
        "dossier": {
            "dossier_id": dossier.dossier_id,
            "kind": dossier.kind,
            "target_id": dossier.target_id,
            "title": dossier.title,
            "category_focus": dossier.category_focus,
            "candidate_fragment": dossier.candidate_fragment,
            "schema_excerpt": dossier.schema_excerpt,
            "evidence": _serialize_evidence(dossier),
            "metadata": dossier.metadata,
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _serialize_evidence(dossier: Dossier) -> List[Dict[str, object]]:
    evidence_blocks: List[Dict[str, object]] = []
    for snippet in dossier.evidence:
        evidence_blocks.append(
            {
                "kind": snippet.kind,
                "label": snippet.label,
                "locator": snippet.locator.model_dump(mode="json"),
                "text": snippet.text,
                "payload": snippet.payload,
            }
        )
    return evidence_blocks


def _serialize_judgment(judgment: Judgment) -> Dict[str, object]:
    return {
        "label": judgment.label,
        "counsel_name": judgment.counsel_name,
        "dossier_id": judgment.dossier_id,
        "category": judgment.category,
        "node_id": judgment.node_id,
        "severity": judgment.severity,
        "title": judgment.title,
        "problem": judgment.problem,
        "evidence_refs": judgment.evidence_refs,
        "recommended_fix": judgment.recommended_fix,
        "confidence": judgment.confidence,
        "metadata": judgment.metadata,
    }
