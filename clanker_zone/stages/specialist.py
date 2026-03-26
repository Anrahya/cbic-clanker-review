from __future__ import annotations

from typing import List

from ..models import CounselSpec, CouncilTask, Dossier


def build_specialist_tasks(dossiers: List[Dossier], roster: List[CounselSpec]) -> List[CouncilTask]:
    tasks: List[CouncilTask] = []
    specialists = [counsel for counsel in roster if counsel.stage == "specialist"]
    for dossier in dossiers:
        for counsel in specialists:
            overlap = sorted(set(dossier.category_focus).intersection(counsel.categories))
            if not overlap:
                continue
            tasks.append(
                CouncilTask(
                    task_id=f"specialist-{counsel.name}-{dossier.dossier_id}",
                    stage="specialist",
                    counsel_name=counsel.name,
                    dossier_id=dossier.dossier_id,
                    prompt_key=counsel.prompt_key,
                    categories=overlap,
                    payload={"target_id": dossier.target_id, "kind": dossier.kind},
                )
            )
    return tasks

