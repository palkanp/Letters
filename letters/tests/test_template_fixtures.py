"""Guards for the shipped Letters Template fixtures.

These run without a live site — they validate the JSON fixture file directly so
a bad template (e.g. one reintroducing the discontinued ``rich_text`` block, or
referencing an unknown block type) fails CI immediately.
"""
import json
import os

import pytest

from letters.letters.utils.block_renderers import RENDERER_MAP

FIXTURE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "letters", "fixtures", "letters_template.json",
)

# "rich_text" was merged into "text" and is intentionally NOT allowed in
# templates, even though the renderer keeps a backward-compat alias.
DISCONTINUED_TYPES = {"rich_text"}
ALLOWED_TYPES = set(RENDERER_MAP) - DISCONTINUED_TYPES


def _load_fixtures():
    with open(FIXTURE) as f:
        return json.load(f)


def _iter_block_types(blocks):
    for blk in blocks:
        yield blk.get("type")
        for col in blk.get("columns", []) or []:
            yield from _iter_block_types(col.get("blocks", []) or [])
        yield from _iter_block_types(blk.get("children", []) or [])


def test_fixture_file_parses():
    data = _load_fixtures()
    assert isinstance(data, list) and data, "fixture file must be a non-empty list"
    for tpl in data:
        assert tpl["doctype"] == "Letters Template"
        json.loads(tpl["blocks_json"])  # must be valid JSON


def test_no_discontinued_block_types():
    for tpl in _load_fixtures():
        blocks = json.loads(tpl["blocks_json"])
        types = set(_iter_block_types(blocks))
        bad = types & DISCONTINUED_TYPES
        assert not bad, f"Template '{tpl['title']}' uses discontinued block(s): {bad}. Use 'text' instead."


def test_only_known_block_types():
    for tpl in _load_fixtures():
        blocks = json.loads(tpl["blocks_json"])
        for t in _iter_block_types(blocks):
            assert t in ALLOWED_TYPES, f"Template '{tpl['title']}' uses unknown block type '{t}'"


def test_single_font_per_template():
    """A template must not mix typefaces — every font-bearing block shares one font."""
    no_font = {"divider", "spacer", "social"}
    for tpl in _load_fixtures():
        blocks = json.loads(tpl["blocks_json"])
        fonts = {
            blk.get("props", {}).get("font_family")
            for blk in blocks
            if blk.get("type") not in no_font and blk.get("props", {}).get("font_family")
        }
        assert len(fonts) <= 1, f"Template '{tpl['title']}' mixes fonts: {fonts}"
