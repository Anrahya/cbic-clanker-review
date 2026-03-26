from __future__ import annotations

from .common import build_finding, node_text, source_text
from ..models import CheckContext, CheckResult
from ..raw_source.locators import extract_locator_mentions, normalize_text


def run(context: CheckContext) -> CheckResult:
    result = CheckResult()
    for node in context.indexed_rule.nodes.values():
        source_fragment = source_text(context, node) or node_text(node)
        if not source_fragment:
            continue
        expected_mentions = extract_locator_mentions(source_fragment)
        seen_pairs: set[tuple[str, str]] = set()
        extracted_refs = node.cross_refs or []
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
    return result

