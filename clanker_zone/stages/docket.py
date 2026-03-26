from __future__ import annotations

from typing import List

from ..models import CouncilTask, Dossier


def build_docket_tasks(dossiers: List[Dossier]) -> List[CouncilTask]:
    return [
        CouncilTask(
            task_id=f"docket-{dossier.dossier_id}",
            stage="docket",
            counsel_name="docket_clerk",
            dossier_id=dossier.dossier_id,
            prompt_key="core.docket",
            categories=dossier.category_focus,
            payload={"target_id": dossier.target_id, "kind": dossier.kind},
        )
        for dossier in dossiers
    ]

