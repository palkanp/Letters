from __future__ import annotations

import json
from typing import Any


class DesignTreeProcessor:
    """Validates and normalises the blocks JSON tree before compilation."""

    VALID_BLOCK_TYPES = {
        "hero", "text", "image", "image_text", "button",
        "columns", "container", "section_label", "divider", "footer",
        "spacer", "quote", "social", "product_card", "video_thumb",
    }

    def __init__(self, blocks_json: str | list):
        if isinstance(blocks_json, str):
            self._tree = json.loads(blocks_json)
        else:
            self._tree = blocks_json

    def validate(self) -> None:
        if not isinstance(self._tree, list):
            raise ValueError("Design tree must be a list of blocks")
        for block in self._tree:
            self._validate_block(block)

    def get_tree(self) -> list:
        return self._tree

    def _validate_block(self, block: dict[str, Any]) -> None:
        block_type = block.get("type")
        if block_type not in self.VALID_BLOCK_TYPES:
            raise ValueError(f"Unknown block type: {block_type!r}")
        # Recurse into container children so nested blocks are also validated
        for child in block.get("children") or []:
            self._validate_block(child)
