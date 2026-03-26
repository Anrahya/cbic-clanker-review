from __future__ import annotations

from collections import Counter

from ..models import Finding


def severity_counts(findings: list[Finding]) -> Counter[str]:
    return Counter(finding.severity for finding in findings)

