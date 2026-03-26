from __future__ import annotations

from typing import List

from ..models import CounselSpec, CouncilTask, Dossier


def build_arbiter_tasks(dossiers: List[Dossier], roster: List[CounselSpec]) -> List[CouncilTask]:
    arbiter = next((counsel for counsel in roster if counsel.stage == "arbiter"), None)
    if arbiter is None:
        return []
    return [
        CouncilTask(
            task_id=f"arbiter-{dossier.dossier_id}",
            stage="arbiter",
            counsel_name=arbiter.name,
            dossier_id=dossier.dossier_id,
            prompt_key=arbiter.prompt_key,
            categories=dossier.category_focus,
            payload={"target_id": dossier.target_id, "kind": dossier.kind},
        )
        for dossier in dossiers
    ]

