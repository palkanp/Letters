"""
Tests for letters/utils/block_renderers.py

Run with:  pytest letters/tests/test_block_renderers.py -v
(from the repo root, no Frappe bench required)
"""
import sys
import os

# Make the letters package importable without a Frappe bench
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from letters.letters.utils.block_renderers import (
    _safe_url,
    _hex_to_rgba,
    _padding,
    _spacing_wrapper,
    HeroRenderer,
    TextRenderer,
    ImageRenderer,
    ButtonRenderer,
    ColumnsRenderer,
    ContainerRenderer,
    FooterRenderer,
    SpacerRenderer,
    DividerRenderer,
    QuoteRenderer,
    SocialRenderer,
    ProductCardRenderer,
    VideoThumbRenderer,
    RENDERER_MAP,
)


# ── _safe_url ─────────────────────────────────────────────────────────────────

class TestSafeUrl:
    def test_plain_https_url_passes_through(self):
        assert _safe_url("https://example.com") == "https://example.com"

    def test_plain_http_url_passes_through(self):
        assert _safe_url("http://example.com/path?a=1&b=2") == "http://example.com/path?a=1&amp;b=2"

    def test_ampersand_is_escaped(self):
        result = _safe_url("https://example.com/?a=1&b=2")
        assert "&amp;" in result

    def test_javascript_scheme_blocked(self):
        assert _safe_url("javascript:alert(1)") == "#"

    def test_javascript_scheme_case_insensitive(self):
        assert _safe_url("JaVaScRiPt:alert(1)") == "#"

    def test_javascript_with_leading_null_bytes_blocked(self):
        assert _safe_url("\x00javascript:alert(1)") == "#"

    def test_javascript_with_leading_whitespace_blocked(self):
        assert _safe_url("  \t\njavascript:alert(1)") == "#"

    def test_data_uri_blocked(self):
        assert _safe_url("data:text/html,<script>alert(1)</script>") == "#"

    def test_vbscript_blocked(self):
        assert _safe_url("vbscript:MsgBox(1)") == "#"

    def test_empty_string_returns_empty(self):
        assert _safe_url("") == ""

    def test_none_returns_empty(self):
        assert _safe_url(None) == ""

    def test_hash_anchor_passes_through(self):
        assert _safe_url("#") == "#"

    def test_relative_url_passes_through(self):
        assert _safe_url("/about") == "/about"


# ── _hex_to_rgba ──────────────────────────────────────────────────────────────

class TestHexToRgba:
    def test_six_digit_hex(self):
        assert _hex_to_rgba("#374151", 0.1) == "rgba(55,65,81,0.1)"

    def test_three_digit_hex_expands(self):
        assert _hex_to_rgba("#fff", 1) == "rgba(255,255,255,1)"

    def test_without_hash(self):
        assert _hex_to_rgba("111827", 0.5) == "rgba(17,24,39,0.5)"

    def test_invalid_hex_returns_fallback(self):
        result = _hex_to_rgba("ZZZZZZ", 0.2)
        assert result == "rgba(0,0,0,0.2)"

    def test_empty_string_returns_fallback(self):
        assert _hex_to_rgba("", 0.3) == "rgba(0,0,0,0.3)"


# ── _padding ──────────────────────────────────────────────────────────────────

class TestPadding:
    def test_defaults(self):
        assert _padding({}) == "20px 32px 20px 32px"

    def test_custom_values(self):
        props = {"padding_top": 10, "padding_right": 8, "padding_bottom": 6, "padding_left": 4}
        assert _padding(props) == "10px 8px 6px 4px"

    def test_partial_override(self):
        result = _padding({"padding_top": 0})
        assert result.startswith("0px ")

    def test_custom_defaults(self):
        assert _padding({}, dt=40, dr=40, db=40, dl=40) == "40px 40px 40px 40px"


# ── _spacing_wrapper ──────────────────────────────────────────────────────────

class TestSpacingWrapper:
    def test_no_spacing_returns_inner_unchanged(self):
        inner = "<p>hello</p>"
        assert _spacing_wrapper(inner, {}) == inner

    def test_zero_spacing_returns_inner_unchanged(self):
        inner = "<p>hello</p>"
        assert _spacing_wrapper(inner, {"spacing_top": 0, "spacing_bottom": 0}) == inner

    def test_spacing_wraps_in_table(self):
        result = _spacing_wrapper("<p>x</p>", {"spacing_top": 20, "spacing_bottom": 10})
        assert "padding-top:20px" in result
        assert "padding-bottom:10px" in result
        assert "<p>x</p>" in result


# ── HeroRenderer ──────────────────────────────────────────────────────────────

class TestHeroRenderer:
    def _r(self, props):
        return HeroRenderer().render({"type": "hero", "props": props})

    def test_renders_heading(self):
        html = self._r({"heading": "Welcome!"})
        assert "Welcome!" in html

    def test_renders_subheading(self):
        html = self._r({"heading": "Hi", "subheading": "This is a sub"})
        assert "This is a sub" in html

    def test_xss_heading_escaped(self):
        html = self._r({"heading": "<script>alert(1)</script>"})
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_default_background_color(self):
        html = self._r({})
        assert "#ffffff" in html

    def test_custom_background_color(self):
        html = self._r({"background_color": "#ff0000"})
        assert "#ff0000" in html


# ── TextRenderer ─────────────────────────────────────────────────────────────

class TestTextRenderer:
    def _r(self, props):
        return TextRenderer().render({"type": "text", "props": props})

    def test_renders_content(self):
        assert "Hello world" in self._r({"content": "Hello world"})

    def test_xss_content_escaped(self):
        html = self._r({"content": '<img src=x onerror="alert(1)">'})
        assert "<img" not in html
        assert "&lt;img" in html

    def test_default_font_size(self):
        assert "15px" in self._r({})

    def test_custom_align(self):
        assert 'align="right"' in self._r({"align": "right"})


# ── ImageRenderer ─────────────────────────────────────────────────────────────

class TestImageRenderer:
    def _r(self, props):
        return ImageRenderer().render({"type": "image", "props": props})

    def test_empty_url_returns_empty_string(self):
        assert self._r({}) == ""
        assert self._r({"image_url": ""}) == ""

    def test_renders_img_tag(self):
        html = self._r({"image_url": "https://example.com/img.png"})
        assert "<img" in html
        assert "https://example.com/img.png" in html

    def test_caption_rendered_when_present(self):
        html = self._r({"image_url": "https://x.com/a.png", "caption": "My caption"})
        assert "My caption" in html

    def test_no_caption_row_when_empty(self):
        html = self._r({"image_url": "https://x.com/a.png"})
        # caption row has a specific class pattern; if no caption the <tr> for it is absent
        assert "My caption" not in html


# ── ButtonRenderer ────────────────────────────────────────────────────────────

class TestButtonRenderer:
    def _r(self, props):
        return ButtonRenderer().render({"type": "button", "props": props})

    def test_renders_label(self):
        assert "Click Me" in self._r({"label": "Click Me"})

    def test_renders_valid_url(self):
        html = self._r({"url": "https://shop.example.com"})
        assert "https://shop.example.com" in html

    def test_javascript_url_blocked(self):
        html = self._r({"url": "javascript:steal()"})
        assert "javascript:" not in html
        assert 'href="#"' in html

    def test_data_uri_blocked(self):
        html = self._r({"url": "data:text/html,<h1>pwned</h1>"})
        assert "data:" not in html
        assert 'href="#"' in html

    def test_xss_label_escaped(self):
        html = self._r({"label": "<b>Bold</b>"})
        assert "<b>" not in html
        assert "&lt;b&gt;" in html

    def test_default_label_fallback(self):
        assert "Click here" in self._r({})


# ── ColumnsRenderer ───────────────────────────────────────────────────────────

class TestColumnsRenderer:
    def _r(self, props):
        return ColumnsRenderer().render({"type": "columns", "props": props})

    def test_renders_column_heading(self):
        html = self._r({"columns": [{"heading": "Col 1", "text": "", "button_label": ""}]})
        assert "Col 1" in html

    def test_column_button_url_javascript_blocked(self):
        html = self._r({
            "columns": [{
                "heading": "", "text": "body", "button_label": "Go",
                "button_url": "javascript:alert(1)",
            }]
        })
        assert "javascript:" not in html
        assert 'href="#"' in html

    def test_xss_column_heading_escaped(self):
        html = self._r({"columns": [{"heading": "<script>x</script>", "text": "", "button_label": ""}]})
        assert "<script>" not in html


# ── SocialRenderer ────────────────────────────────────────────────────────────

class TestSocialRenderer:
    def _r(self, props):
        return SocialRenderer().render({"type": "social", "props": props})

    def test_empty_links_returns_empty_string(self):
        assert self._r({}) == ""

    def test_renders_present_links(self):
        html = self._r({"x_url": "https://twitter.com/foo"})
        assert "https://twitter.com/foo" in html
        assert "X / Twitter" in html

    def test_javascript_social_url_blocked(self):
        html = self._r({"linkedin_url": "javascript:alert(1)"})
        assert "javascript:" not in html
        # When the only URL is dangerous, the rendered link uses '#'
        assert 'href="#"' in html

    def test_label_only_no_emoji(self):
        """Social pills must be label-only — no unicode/emoji icons."""
        html = self._r({"github_url": "https://github.com/foo"})
        assert "𝕏" not in html
        assert "◎" not in html
        assert "▶" not in html


# ── ProductCardRenderer ───────────────────────────────────────────────────────

class TestProductCardRenderer:
    def _r(self, props):
        return ProductCardRenderer().render({"type": "product_card", "props": props})

    def test_renders_title(self):
        assert "Cool Widget" in self._r({"title": "Cool Widget"})

    def test_renders_price(self):
        assert "$49.99" in self._r({"price": "$49.99"})

    def test_button_url_javascript_blocked(self):
        html = self._r({"button_label": "Buy", "button_url": "javascript:steal()"})
        assert "javascript:" not in html

    def test_no_image_html_when_url_empty(self):
        html = self._r({"title": "T", "image_url": ""})
        # <img> should NOT appear when no image_url
        assert "<img" not in html


# ── VideoThumbRenderer ────────────────────────────────────────────────────────

class TestVideoThumbRenderer:
    def _r(self, props):
        return VideoThumbRenderer().render({"type": "video_thumb", "props": props})

    def test_no_thumbnail_returns_empty(self):
        assert self._r({}) == ""

    def test_renders_thumbnail_link(self):
        html = self._r({
            "thumbnail_url": "https://img.yt/thumb.jpg",
            "video_url": "https://youtube.com/watch?v=abc",
        })
        assert "https://img.yt/thumb.jpg" in html
        assert "https://youtube.com/watch?v=abc" in html

    def test_javascript_video_url_blocked(self):
        html = self._r({
            "thumbnail_url": "https://img.yt/thumb.jpg",
            "video_url": "javascript:steal()",
        })
        assert "javascript:" not in html
        assert 'href="#"' in html

    def test_caption_rendered(self):
        html = self._r({
            "thumbnail_url": "https://img.yt/thumb.jpg",
            "video_url": "https://yt.com/v",
            "caption": "Watch the demo",
        })
        assert "Watch the demo" in html


# ── SpacerRenderer ────────────────────────────────────────────────────────────

class TestSpacerRenderer:
    def test_default_height(self):
        html = SpacerRenderer().render({"type": "spacer", "props": {}})
        assert "height:32px" in html

    def test_custom_height(self):
        html = SpacerRenderer().render({"type": "spacer", "props": {"height": 64}})
        assert "height:64px" in html


# ── DividerRenderer ───────────────────────────────────────────────────────────

class TestDividerRenderer:
    def test_renders_hr(self):
        html = DividerRenderer().render({"type": "divider", "props": {}})
        assert "<hr" in html

    def test_custom_color(self):
        html = DividerRenderer().render({"type": "divider", "props": {"border_color": "#aabbcc"}})
        assert "#aabbcc" in html


# ── FooterRenderer ────────────────────────────────────────────────────────────

class TestFooterRenderer:
    def test_renders_text(self):
        html = FooterRenderer().render({"type": "footer", "props": {"text": "Unsubscribe"}})
        assert "Unsubscribe" in html

    def test_xss_escaped(self):
        html = FooterRenderer().render({"type": "footer", "props": {"text": "<script>x</script>"}})
        assert "<script>" not in html


# ── QuoteRenderer ─────────────────────────────────────────────────────────────

class TestQuoteRenderer:
    def _r(self, props):
        return QuoteRenderer().render({"type": "quote", "props": props})

    def test_left_border_style_renders_quote(self):
        assert "Great quote" in self._r({"quote": "Great quote", "style": "left-border"})

    def test_centered_style_renders_quote(self):
        assert "Great quote" in self._r({"quote": "Great quote", "style": "centered"})

    def test_author_and_role_rendered(self):
        html = self._r({"quote": "Q", "author": "Alice", "role": "CEO", "style": "left-border"})
        assert "Alice" in html
        assert "CEO" in html


# ── ContainerRenderer ─────────────────────────────────────────────────────────

class TestContainerRenderer:
    def test_empty_container_returns_empty_string(self):
        block = {"type": "container", "props": {}, "children": []}
        assert ContainerRenderer().render(block) == ""

    def test_renders_child_block(self):
        block = {
            "type": "container",
            "props": {},
            "children": [
                {"type": "text", "props": {"content": "Child text"}}
            ],
        }
        html = ContainerRenderer().render(block)
        assert "Child text" in html

    def test_row_layout_uses_table_cells(self):
        block = {
            "type": "container",
            "props": {"layout": "row"},
            "children": [
                {"type": "text", "props": {"content": "Left"}},
                {"type": "text", "props": {"content": "Right"}},
            ],
        }
        html = ContainerRenderer().render(block)
        assert "Left" in html
        assert "Right" in html
        assert "<td" in html


# ── RENDERER_MAP completeness ─────────────────────────────────────────────────

class TestRendererMap:
    EXPECTED_TYPES = {
        "hero", "text", "image", "image_text", "button", "columns",
        "container", "section_label", "divider", "footer", "spacer",
        "quote", "social", "product_card", "video_thumb",
    }

    def test_all_expected_types_present(self):
        assert self.EXPECTED_TYPES == set(RENDERER_MAP.keys())

    def test_all_renderers_have_render_method(self):
        for name, renderer in RENDERER_MAP.items():
            assert hasattr(renderer, "render"), f"{name} renderer missing .render()"
