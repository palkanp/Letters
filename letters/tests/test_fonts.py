"""
Tests for letters/utils/fonts.py — web font helpers and regression guards.

Covers:
  1. font_stack() resolves system and web fonts
  2. is_web_font() correctly classifies fonts
  3. google_fonts_url() generates correct URLs
  4. google_fonts_link_tags() returns correct <link> HTML
  5. EmailCompiler injects <link> tags when web fonts are used
  6. EmailCompiler emits NO <link> tags when only system fonts are used

Run with:  pytest letters/tests/test_fonts.py -v
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from letters.letters.utils.fonts import (
    WEB_FONT_META,
    FONT_STACKS,
    font_stack,
    is_web_font,
    google_fonts_url,
    google_fonts_link_tags,
)
from letters.letters.utils.email_compiler import EmailCompiler


# ---------------------------------------------------------------------------
# 1. font_stack()
# ---------------------------------------------------------------------------

class TestFontStack:
    def test_system_font_resolved(self):
        assert font_stack({"font_family": "Arial"}, "") == "Arial, Helvetica, sans-serif"

    def test_web_font_resolved(self):
        stack = font_stack({"font_family": "Inter"}, "")
        assert "'Inter'" in stack
        assert "Arial" in stack  # fallback

    def test_unknown_returns_fallback(self):
        assert font_stack({"font_family": "Comic Sans"}, "my-fallback") == "my-fallback"

    def test_empty_returns_fallback(self):
        assert font_stack({}, "fallback") == "fallback"
        assert font_stack({"font_family": ""}, "fallback") == "fallback"
        assert font_stack({"font_family": None}, "fallback") == "fallback"


# ---------------------------------------------------------------------------
# 2. is_web_font()
# ---------------------------------------------------------------------------

class TestIsWebFont:
    def test_all_web_fonts_detected(self):
        for name in WEB_FONT_META:
            assert is_web_font(name), f"{name} should be detected as web font"

    def test_system_fonts_not_web(self):
        for name in ["Arial", "Georgia", "Verdana", "Courier New"]:
            assert not is_web_font(name), f"{name} should NOT be a web font"

    def test_empty_not_web(self):
        assert not is_web_font("")
        assert not is_web_font(None)


# ---------------------------------------------------------------------------
# 3. google_fonts_url()
# ---------------------------------------------------------------------------

class TestGoogleFontsUrl:
    def test_returns_none_for_empty(self):
        assert google_fonts_url([]) is None
        assert google_fonts_url(None) is None

    def test_returns_none_for_system_fonts_only(self):
        assert google_fonts_url(["Arial", "Georgia"]) is None

    def test_valid_url_for_single_web_font(self):
        url = google_fonts_url(["Inter"])
        assert "fonts.googleapis.com" in url
        assert "family=Inter" in url
        assert "wght@" in url
        assert "display=swap" in url

    def test_url_includes_all_declared_weights(self):
        url = google_fonts_url(["Inter"])
        for w in WEB_FONT_META["Inter"]["weights"]:
            assert str(w) in url, f"Weight {w} missing from Google Fonts URL"

    def test_multiple_fonts_in_one_url(self):
        url = google_fonts_url(["Inter", "Poppins"])
        assert "family=Inter" in url
        assert "family=Poppins" in url

    def test_deduplication(self):
        url = google_fonts_url(["Inter", "Inter", "Inter"])
        assert url.count("family=Inter") == 1

    def test_system_fonts_ignored(self):
        url = google_fonts_url(["Arial", "Inter", "Georgia"])
        assert "Arial" not in url
        assert "Georgia" not in url
        assert "Inter" in url


# ---------------------------------------------------------------------------
# 4. google_fonts_link_tags()
# ---------------------------------------------------------------------------

class TestGoogleFontsLinkTags:
    def test_empty_string_for_no_web_fonts(self):
        assert google_fonts_link_tags([]) == ""
        assert google_fonts_link_tags(["Arial"]) == ""

    def test_returns_link_tags_for_web_fonts(self):
        html = google_fonts_link_tags(["Inter"])
        assert '<link rel="preconnect"' in html
        assert '<link rel="stylesheet"' in html
        assert "fonts.googleapis.com" in html

    def test_link_tags_are_valid_html(self):
        html = google_fonts_link_tags(["Inter"])
        # Must be parseable — no unclosed tags, balanced quotes
        assert html.count('"') % 2 == 0
        assert "<link" in html


# ---------------------------------------------------------------------------
# 5. EmailCompiler injects <link> when web fonts are used
# ---------------------------------------------------------------------------

class TestEmailCompilerFontLinks:
    def test_injects_link_tags_for_web_font(self):
        blocks = [{"type": "rich_text", "props": {"font_family": "Inter", "html_content": "<p>Hi</p>"}}]
        html = EmailCompiler(blocks).compile()
        assert "fonts.googleapis.com" in html
        assert "Inter" in html
        # Link tags must be in <head>
        head = html.split("</head>")[0]
        assert "fonts.googleapis.com" in head

    def test_no_link_tags_for_system_fonts(self):
        blocks = [{"type": "rich_text", "props": {"font_family": "Arial", "html_content": "<p>Hi</p>"}}]
        html = EmailCompiler(blocks).compile()
        assert "fonts.googleapis.com" not in html

    def test_no_link_tags_when_no_font_set(self):
        blocks = [{"type": "rich_text", "props": {"html_content": "<p>Hi</p>"}}]
        html = EmailCompiler(blocks).compile()
        assert "fonts.googleapis.com" not in html

    def test_single_url_for_multiple_same_web_font(self):
        blocks = [
            {"type": "rich_text", "props": {"font_family": "Inter", "html_content": "<p>A</p>"}},
            {"type": "rich_text", "props": {"font_family": "Inter", "html_content": "<p>B</p>"}},
        ]
        html = EmailCompiler(blocks).compile()
        assert html.count("family=Inter") == 1

    def test_collects_fonts_from_all_web_font_types(self):
        """Each web font in WEB_FONT_META must trigger a <link> when used."""
        for name in WEB_FONT_META:
            blocks = [{"type": "rich_text", "props": {"font_family": name, "html_content": "<p>x</p>"}}]
            html = EmailCompiler(blocks).compile()
            assert "fonts.googleapis.com" in html, f"No <link> injected for web font '{name}'"


# ---------------------------------------------------------------------------
# 6. WEB_FONT_META sanity — mirrors JS test
# ---------------------------------------------------------------------------

class TestWebFontMeta:
    VALID_WEIGHTS = {100, 200, 300, 400, 500, 600, 700, 800, 900}

    @pytest.mark.parametrize("name,meta", WEB_FONT_META.items())
    def test_weights_are_valid(self, name, meta):
        for w in meta["weights"]:
            assert w in self.VALID_WEIGHTS, f"{name}: weight {w} is not a valid CSS value"

    @pytest.mark.parametrize("name,meta", WEB_FONT_META.items())
    def test_includes_regular_and_bold(self, name, meta):
        assert 400 in meta["weights"], f"{name}: missing 400 (regular)"
        assert 700 in meta["weights"], f"{name}: missing 700 (bold)"

    @pytest.mark.parametrize("name,meta", WEB_FONT_META.items())
    def test_has_google_family_and_fallback(self, name, meta):
        assert meta.get("google_family"), f"{name}: missing google_family"
        assert meta.get("fallback"), f"{name}: missing fallback"

    @pytest.mark.parametrize("name", WEB_FONT_META.keys())
    def test_in_font_stacks(self, name):
        assert name in FONT_STACKS, f"{name} missing from FONT_STACKS"
