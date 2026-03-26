from __future__ import annotations

from typing import List, Optional

from .config import CouncilConfig
from .dossier import build_shared_prefix
from .models import CounselSpec, CouncilRunPlan, CouncilTask, Dossier
from .stages.arbiter import build_arbiter_tasks
from .stages.docket import build_docket_tasks
from .stages.skeptic import build_skeptic_tasks
from .stages.specialist import build_specialist_tasks


class CouncilBuilder:
    def __init__(self, config: CouncilConfig, domain_name: str, roster: List[CounselSpec]) -> None:
        self.config = config
        self.domain_name = domain_name
        self.roster = roster

    def build_plan(
        self,
        *,
        dossiers: List[Dossier],
        constitution: str,
        domain_overview: str,
        output_contract: str,
        metadata: Optional[dict] = None,
    ) -> CouncilRunPlan:
        shared_prefix = build_shared_prefix(constitution, domain_overview, output_contract)
        tasks: List[CouncilTask] = []
        tasks.extend(build_docket_tasks(dossiers))
        tasks.extend(build_specialist_tasks(dossiers, self.roster))
        if self.config.challenge_all_confirmed_issues:
            tasks.extend(build_skeptic_tasks(dossiers, self.roster))
        tasks.extend(build_arbiter_tasks(dossiers, self.roster))
        return CouncilRunPlan(
            council_name=self.config.name,
            domain=self.domain_name,
            shared_prefix=shared_prefix,
            dossiers=dossiers,
            tasks=tasks,
            metadata=metadata or {},
        )
