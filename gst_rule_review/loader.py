from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from .raw_source.fetch import fetch_source_html


def load_json(path: Union[str, Path]) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_text(path: Union[str, Path]) -> str:
    return Path(path).read_text(encoding="utf-8")


def resolve_raw_html(
    raw_path: Optional[Union[str, Path]],
    source_url: Optional[str],
    metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Optional[str]]:
    if raw_path:
        return load_text(raw_path), str(raw_path)
    candidate_url = source_url or (metadata or {}).get("source_url")
    if not candidate_url:
        raise ValueError("Either raw HTML or a source_url must be provided.")
    return fetch_source_html(candidate_url), candidate_url
