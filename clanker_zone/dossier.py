from __future__ import annotations

from typing import Dict

from .models import Dossier


def dossier_map(dossiers: list[Dossier]) -> Dict[str, Dossier]:
    return {dossier.dossier_id: dossier for dossier in dossiers}


def build_shared_prefix(constitution: str, domain_overview: str, output_contract: str) -> str:
    return "\n\n".join(
        section.strip()
        for section in (constitution, domain_overview, output_contract)
        if section and section.strip()
    )

