from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class ReviewConfig(BaseModel):
    tolerate_cbic_spacing_artifacts: bool = True
    allow_textless_structural_nodes: bool = True
    emit_needs_manual_review: bool = True
    min_confirm_confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    strict_mode: bool = False
    cache_dir: Optional[Path] = None
