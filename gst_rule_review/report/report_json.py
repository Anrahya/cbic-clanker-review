from __future__ import annotations

import json

from ..models import ReviewReport


def render_report_json(report: ReviewReport) -> str:
    return json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2)

