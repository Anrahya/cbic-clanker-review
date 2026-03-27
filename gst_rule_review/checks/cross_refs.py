from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from .common import build_finding, node_text, source_text
from ..models import CheckContext, CheckResult
from ..raw_source.locators import extract_locator_mentions, normalize_text


def run(context: CheckContext) -> CheckResult:
    result = CheckResult()

    # Build hint cross-ref lookup (if available)
    hint_xref_index: Dict[str, Dict[str, Any]] = {}
    for hint_xref in context.hint_json.get("cross_ref_hints", []):
        # Index by normalized mention text for fuzzy matching
        mention = normalize_text(str(hint_xref.get("mention_text") or hint_xref.get("text") or ""))
        if mention:
            hint_xref_index[mention] = hint_xref

    for node in context.indexed_rule.nodes.values():
        source_fragment = source_text(context, node) or node_text(node)
        if not source_fragment:
            continue
        expected_mentions = extract_locator_mentions(source_fragment)
        seen_pairs: set[tuple[str, str]] = set()
        extracted_refs = node.cross_refs or []

        # --- Existing: Duplicate cross-references ---
        for ref in extracted_refs:
            mention = normalize_text(str(ref.get("mention_text") or ref.get("source_text") or ref.get("target_text") or ""))
            target = normalize_text(str(ref.get("target_text") or ""))
            pair = (mention, target)
            if pair in seen_pairs:
                result.findings.append(
                    build_finding(
                        issue_id=f"XREF-DUPE-{node.node_id}",
                        category="cross_refs",
                        severity="moderate",
                        title="Duplicate cross-reference emitted for one source mention",
                        problem="The same cross-reference target has been emitted multiple times from the same textual mention.",
                        node=node,
                        raw_source_fragment=source_fragment,
                        why_real_defect="Duplicate graph edges add noise and can distort downstream relationship counts.",
                        recommended_fix="Deduplicate cross_refs by mention and target within a node.",
                        confidence=0.96,
                    )
                )
                break
            seen_pairs.add(pair)

        # --- Existing: Under-resolved target text ---
        for mention in expected_mentions:
            normalized_mention = normalize_text(mention)
            matching = [
                ref
                for ref in extracted_refs
                if normalize_text(str(ref.get("target_text") or "")) == normalized_mention
                or normalize_text(str(ref.get("target_text") or "")) in normalized_mention
            ]
            if not matching:
                continue
            for ref in matching:
                target = normalize_text(str(ref.get("target_text") or ""))
                if target != normalized_mention and target and target in normalized_mention:
                    result.findings.append(
                        build_finding(
                            issue_id=f"XREF-PRECISION-{node.node_id}",
                            category="cross_refs",
                            severity="major",
                            title="Cross-reference target is under-resolved against source mention",
                            problem=f"The source mentions '{normalized_mention}', but the extracted target was reduced to '{target}'.",
                            node=node,
                            raw_source_fragment=source_fragment,
                            why_real_defect="Collapsing a hierarchical reference to a broader target loses legal precision.",
                            recommended_fix="Preserve the most specific target text present in the source, even if deterministic target_id resolution is unavailable.",
                            confidence=0.94,
                        )
                    )
                    break

        # --- NEW: XREF-SUBSUMPTION — one ref subsumes another from same phrase ---
        # Detect when a specific reference (e.g., "sub-rule (2) of rule 8") and a
        # weaker subset reference (e.g., "sub-rule (2)") are both emitted from the
        # same source mention. The weaker ref is redundant noise.
        if len(extracted_refs) > 1:
            targets_with_idx = [
                (idx, normalize_text(str(ref.get("target") or ref.get("target_text") or "")))
                for idx, ref in enumerate(extracted_refs)
            ]
            flagged_indices: Set[int] = set()

            for i, (idx_i, target_i) in enumerate(targets_with_idx):
                if not target_i or idx_i in flagged_indices:
                    continue
                for j, (idx_j, target_j) in enumerate(targets_with_idx):
                    if i == j or not target_j or idx_j in flagged_indices:
                        continue
                    # Check if target_j is a proper substring of target_i
                    # (target_i is the more specific one)
                    if target_j in target_i and target_j != target_i:
                        # Verify they come from the same source phrase by checking
                        # if the longer target's context contains the shorter target
                        ref_i = extracted_refs[idx_i]
                        ref_j = extracted_refs[idx_j]
                        context_i = normalize_text(str(ref_i.get("context") or ""))
                        context_j = normalize_text(str(ref_j.get("context") or ""))
                        # Same phrase if: shorter ref's context contains the longer
                        # target, or the contexts significantly overlap
                        same_phrase = (
                            target_i in context_j
                            or (context_i and context_j and (
                                context_i in context_j or context_j in context_i
                            ))
                        )
                        if same_phrase:
                            # Flag the weaker (shorter) ref as subsumed
                            flagged_indices.add(idx_j)
                            ref_type_j = ref_j.get("target_type", "")
                            result.findings.append(
                                build_finding(
                                    issue_id=f"XREF-SUBSUMPTION-{node.node_id}-{idx_j}",
                                    category="cross_refs",
                                    severity="moderate",
                                    title="Cross-reference over-emits a weaker subset from the same source mention",
                                    problem=(
                                        f"The source mentions '{target_i}', which was correctly captured. "
                                        f"But a second, weaker ref '{target_j}' ({ref_type_j}) was also "
                                        f"emitted from the same phrase. This second ref is both redundant "
                                        f"and under-resolved."
                                    ),
                                    node=node,
                                    raw_source_fragment=source_fragment,
                                    why_real_defect=(
                                        "One source mention should not become a duplicated weaker edge. "
                                        "The redundant ref adds noise to the cross-reference graph and "
                                        "misrepresents the legal reference's specificity."
                                    ),
                                    recommended_fix=(
                                        "Remove the weaker cross-ref. The specific reference already "
                                        "captures the legal citation."
                                    ),
                                    confidence=0.91,
                                )
                            )

        # --- NEW: XREF-HINT-TARGET — validate target_id against hint ---
        if hint_xref_index:
            for ref in extracted_refs:
                extracted_target_id = ref.get("target_id")
                if not extracted_target_id:
                    continue
                # Try to find a matching hint by target text
                ref_target = normalize_text(str(ref.get("target") or ref.get("target_text") or ""))
                hint_entry = hint_xref_index.get(ref_target)
                if not hint_entry:
                    continue
                hint_target_id = hint_entry.get("target_id")
                if hint_target_id and str(hint_target_id) != str(extracted_target_id):
                    result.findings.append(
                        build_finding(
                            issue_id=f"XREF-HINT-TARGET-{node.node_id}",
                            category="cross_refs",
                            severity="moderate",
                            title="Cross-ref target_id does not match CBIC-resolved hint",
                            problem=(
                                f"The extracted target_id is '{extracted_target_id}', but the "
                                f"CBIC hint resolves this reference to target_id '{hint_target_id}'."
                            ),
                            node=node,
                            raw_source_fragment=source_fragment,
                            why_real_defect=(
                                "The hint target_id comes from the CBIC hyperlink, which is the "
                                "authoritative resolution. A mismatch means the cross-reference "
                                "graph points to the wrong entity."
                            ),
                            recommended_fix="Update the target_id to match the CBIC-resolved value from the hint.",
                            confidence=0.88,
                        )
                    )

    return result

