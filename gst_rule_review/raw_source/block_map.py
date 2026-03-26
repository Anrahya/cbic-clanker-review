from __future__ import annotations

from ..models import RawSourceModel, SourceBlock
from .locators import normalize_text


def get_blocks_by_ids(source: RawSourceModel, block_ids: list[int]) -> list[SourceBlock]:
    block_map = {block.block_id: block for block in source.blocks}
    return [block_map[block_id] for block_id in block_ids if block_id in block_map]


def get_combined_text(source: RawSourceModel, block_ids: list[int], normalized: bool = False) -> str:
    blocks = get_blocks_by_ids(source, block_ids)
    values = [block.normalized_text if normalized else block.text for block in blocks]
    return normalize_text(" ".join(value for value in values if value)) if normalized else "\n".join(
        value for value in values if value
    )

