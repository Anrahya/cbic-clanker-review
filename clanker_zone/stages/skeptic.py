from __future__ import annotations

from typing import List

from ..models import CounselSpec, CouncilTask, Dossier


def build_skeptic_tasks(dossiers: List[Dossier], roster: List[CounselSpec]) -> List[CouncilTask]:
    skeptic = next((counsel for counsel in roster if counsel.stage == "skeptic"), None)
    if skeptic is None:
        return []
    return [
        CouncilTask(
            task_id=f"skeptic-{dossier.dossier_id}",
            stage="skeptic",
            counsel_name=skeptic.name,
            dossier_id=dossier.dossier_id,
            prompt_key=skeptic.prompt_key,
            categories=dossier.category_focus,
            payload={"target_id": dossier.target_id, "kind": dossier.kind},
        )
        for dossier in dossiers
    ]

