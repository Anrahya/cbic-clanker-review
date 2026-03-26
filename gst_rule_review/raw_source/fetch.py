from __future__ import annotations

from urllib.request import Request, urlopen


def fetch_source_html(source_url: str) -> str:
    request = Request(
        source_url,
        headers={
            "User-Agent": "gst-rule-review/0.1 (+source-faithful deterministic reviewer)"
        },
    )
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")

