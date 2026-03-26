from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CouncilConfig(BaseModel):
    name: str = "clanker zone"
    strict_evidence_mode: bool = True
    challenge_all_confirmed_issues: bool = True
    emit_manual_review: bool = True
    min_confirm_confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    shared_prefix_version: str = "v1"
    provider_name: str = "minimax"
    model_name: str = "MiniMax-M2.7"
    max_output_tokens: int = 4096
    temperature: float = Field(default=0.1, gt=0.0, le=1.0)
    api_key_env: str = "MINIMAX_API_KEY"
    explicit_api_key: Optional[str] = None

