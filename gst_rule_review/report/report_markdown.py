from __future__ import annotations

from ..models import ReviewReport


def render_report_markdown(report: ReviewReport) -> str:
    lines = ["# GST Rule Review Report", ""]
    lines.append("## Confirmed issues")
    if not report.confirmed_issues:
        lines.append("- None.")
    else:
        for issue in report.confirmed_issues:
            lines.append(
                f"- **{issue.issue_id} | {issue.severity} | {issue.category}**: {issue.title} "
                f"(node `{issue.node_id or 'n/a'}`)"
            )
            lines.append(f"  Problem: {issue.problem}")
            if issue.raw_source_fragment:
                lines.append(f"  Source: `{issue.raw_source_fragment}`")
            if issue.why_real_defect:
                lines.append(f"  Why real defect: {issue.why_real_defect}")
            if issue.recommended_fix:
                lines.append(f"  Fix: {issue.recommended_fix}")
    lines.append("")
    lines.append("## Likely false positives / acceptable source-faithful artifacts")
    if not report.likely_false_positives:
        lines.append("- None.")
    else:
        for item in report.likely_false_positives:
            lines.append(f"- **{item.title}**: {item.reason}")
            if item.raw_source_fragment:
                lines.append(f"  Source: `{item.raw_source_fragment}`")
    lines.append("")
    lines.append("## Overall verdict")
    lines.append(f"- **{report.overall_verdict.status}**: {report.overall_verdict.summary}")
    return "\n".join(lines) + "\n"

