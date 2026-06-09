"""
Tests for letters/utils/design_tree_processor.py

Run with:  pytest letters/tests/test_design_tree_processor.py -v
"""
import sys
import os
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from letters.letters.utils.design_tree_processor import DesignTreeProcessor


def make_block(block_type, **extra):
    b = {"type": block_type}
    b.update(extra)
    return b


# ── Constructor ───────────────────────────────────────────────────────────────

class TestConstructor:
    def test_accepts_list_directly(self):
        tree = [make_block("text")]
        dtp = DesignTreeProcessor(tree)
        assert dtp.get_tree() == tree

    def test_accepts_json_string(self):
        tree = [make_block("text")]
        dtp = DesignTreeProcessor(json.dumps(tree))
        assert dtp.get_tree() == tree

    def test_empty_list_accepted(self):
        dtp = DesignTreeProcessor([])
        assert dtp.get_tree() == []


# ── validate — top-level ──────────────────────────────────────────────────────

class TestValidateTopLevel:
    def test_non_list_raises(self):
        dtp = DesignTreeProcessor.__new__(DesignTreeProcessor)
        dtp._tree = {"type": "text"}           # dict, not list
        with pytest.raises(ValueError, match="must be a list"):
            dtp.validate()

    def test_unknown_top_level_type_raises(self):
        dtp = DesignTreeProcessor([{"type": "unknown_block"}])
        with pytest.raises(ValueError, match="Unknown block type"):
            dtp.validate()

    def test_all_valid_types_pass(self):
        valid_types = [
            "hero", "text", "image", "image_text", "button",
            "columns", "container", "section_label", "divider", "footer",
            "spacer", "quote", "social", "product_card", "video_thumb",
        ]
        tree = [make_block(t) for t in valid_types]
        DesignTreeProcessor(tree).validate()   # must not raise

    def test_mixed_valid_and_invalid_raises(self):
        tree = [make_block("text"), make_block("not_a_real_block")]
        with pytest.raises(ValueError):
            DesignTreeProcessor(tree).validate()


# ── validate — nested children (H-04 regression) ─────────────────────────────

class TestValidateChildren:
    def test_valid_children_pass(self):
        block = make_block("container", children=[make_block("text"), make_block("image")])
        DesignTreeProcessor([block]).validate()  # must not raise

    def test_unknown_child_type_raises(self):
        """H-04: DesignTreeProcessor must recurse into container children."""
        block = make_block("container", children=[{"type": "malicious_block"}])
        with pytest.raises(ValueError, match="Unknown block type.*malicious_block"):
            DesignTreeProcessor([block]).validate()

    def test_deeply_nested_unknown_raises(self):
        inner = make_block("container", children=[{"type": "bad_nested"}])
        outer = make_block("container", children=[inner])
        with pytest.raises(ValueError, match="Unknown block type.*bad_nested"):
            DesignTreeProcessor([outer]).validate()

    def test_deeply_nested_valid_passes(self):
        inner = make_block("container", children=[make_block("text")])
        outer = make_block("container", children=[inner])
        DesignTreeProcessor([outer]).validate()  # must not raise

    def test_children_none_treated_as_empty(self):
        block = make_block("container", children=None)
        DesignTreeProcessor([block]).validate()  # must not raise

    def test_missing_children_key_treated_as_empty(self):
        block = make_block("container")          # no "children" key
        DesignTreeProcessor([block]).validate()  # must not raise


# ── get_tree ──────────────────────────────────────────────────────────────────

class TestGetTree:
    def test_returns_parsed_tree(self):
        tree = [make_block("hero"), make_block("text")]
        assert DesignTreeProcessor(tree).get_tree() == tree

    def test_json_string_is_parsed(self):
        tree = [make_block("footer")]
        assert DesignTreeProcessor(json.dumps(tree)).get_tree() == tree
