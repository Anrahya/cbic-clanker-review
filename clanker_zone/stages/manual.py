from typing import List

from ..models import Dossier, RuleSynthesisReport
from ..provider.base import LLMProvider
from ..domains.gst.prompts import GST_PROMPT_REGISTRY, get_shared_prefix

def apply_manual_review_summarizer(
    report: RuleSynthesisReport,
    dossiers: List[Dossier],
    provider: LLMProvider,
) -> RuleSynthesisReport:
    if not report.manual_review_issues:
        return report

    dossier_map = {d.dossier_id: d for d in dossiers}
    system_prompt = get_shared_prefix()
    instructions = GST_PROMPT_REGISTRY.get("gst.manual_review", "")

    for issue in report.manual_review_issues:
        dossier = dossier_map.get(issue.dossier_id)
        if not dossier:
            continue

        c_frag = dossier.candidate_fragment
        
        user_prompt = (
            f"{instructions}\n\n"
            f"=== TARGET NODE ===\n"
            f"ID: {dossier.target_id}\n"
            f"Title: {c_frag.get('title', 'Unknown')}\n"
            f"Display Label: {c_frag.get('display_label', 'None')}\n\n"
            f"=== CANDIDATE ISSUE ===\n"
            f"Title: {issue.title}\n"
            f"Problem: {issue.problem}\n"
            f"Category: {issue.category}\n"
        )

        request = provider.build_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            metadata={"stage": "manual", "issue_id": issue.issue_id}
        )
        
        try:
            response = provider.invoke(request)
            if response.blocks:
                text = response.blocks[0].text
                if text:
                    issue.metadata["manual_instruction"] = text.strip().replace("\n", " ")
        except Exception as e:
            # Do not fail report generation if summarizer fails
            issue.metadata["manual_instruction"] = f"Failed to generate summary: {str(e)}"

    return report
