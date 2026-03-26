from __future__ import annotations

from .common import build_finding
from ..models import CheckContext, CheckResult


def run(context: CheckContext) -> CheckResult:
    result = CheckResult()
    for node in context.indexed_rule.nodes.values():
        if node.effective_from and node.effective_until and node.effective_until < node.effective_from:
            result.findings.append(
                build_finding(
                    issue_id=f"CHRON-{node.node_id}",
                    category="chronology",
                    severity="major",
                    title="Node chronology is internally inconsistent",
                    problem="effective_until is earlier than effective_from.",
                    node=node,
                    raw_source_fragment="",
                    why_real_defect="Internal date inversion breaks lifecycle semantics for the extracted version.",
                    recommended_fix="Correct the node chronology so effective_from is not later than effective_until.",
                    confidence=0.98,
                )
            )
    return result

