from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Union

import json


def load_rule_json(path: Union[str, Path]) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)
