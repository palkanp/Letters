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
    _abs_image_src,
    _padding,
    _spacing_wrapper,
    _sanitize_rich_html,
    HeroRenderer,
    ImageRenderer,
    ImageTextRenderer,
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
    HeaderRenderer,
    RichTextRenderer,
    LinkListRenderer,
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


# ── _abs_image_src ────────────────────────────────────────────────────────────

class TestAbsImageSrc:
    def test_absolute_https_unchanged(self):
        assert _abs_image_src("https://cdn.example.com/a.png") == "https://cdn.example.com/a.png"

    def test_absolute_http_unchanged(self):
        assert _abs_image_src("http://example.com/a.png") == "http://example.com/a.png"

    def test_protocol_relative_unchanged(self):
        assert _abs_image_src("//cdn.example.com/a.png") == "//cdn.example.com/a.png"

    def test_data_uri_unchanged(self):
        assert _abs_image_src("data:image/png;base64,AAAA") == "data:image/png;base64,AAAA"

    def test_empty_returns_empty(self):
        assert _abs_image_src("") == ""
        assert _abs_image_src(None) == ""

    def test_ampersand_in_absolute_url_is_escaped(self):
        assert "&amp;" in _abs_image_src("https://x.test/a.png?w=1&h=2")

    def test_relative_path_outside_frappe_stays_relative(self):
        # Without a Frappe runtime get_url() is unavailable, so the path is left
        # as-is rather than crashing. (In production it becomes absolute.)
        assert _abs_image_src("/files/x.png") == "/files/x.png"


# ── _padding ──────────────────────────────────────────────────────────────────

class TestPadding:
    def test_defaults(self):
        # _padding(props, dt=20, dr=16, db=20, dl=16) — the signature's own defaults
        assert _padding({}) == "20px 16px 20px 16px"

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
        assert "padding:20px 0px 10px 0px;" in result
        assert "<p>x</p>" in result

    def test_left_right_spacing(self):
        result = _spacing_wrapper("<p>x</p>", {"spacing_left": 16, "spacing_right": 8})
        assert "padding:0px 8px 0px 16px;" in result
        assert "<p>x</p>" in result

    def test_all_four_sides(self):
        result = _spacing_wrapper("<p>x</p>", {"spacing_top": 10, "spacing_bottom": 20, "spacing_left": 8, "spacing_right": 4})
        assert "padding:10px 4px 20px 8px;" in result

    def test_zero_left_right_returns_inner_unchanged(self):
        inner = "<p>hello</p>"
        assert _spacing_wrapper(inner, {"spacing_left": 0, "spacing_right": 0}) == inner


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

    def test_letter_spacing_applied(self):
        html = self._r({"label": "Buy", "letter_spacing": "0.1em"})
        assert "letter-spacing:0.1em;" in html

    def test_letter_spacing_normal_omitted(self):
        html = self._r({"label": "Buy", "letter_spacing": "normal"})
        assert "letter-spacing" not in html

    def test_background_color_applied(self):
        html = self._r({"label": "Buy", "background_color": "#f0f0f0"})
        assert "background-color:#f0f0f0;" in html

    def test_transparent_background_omitted(self):
        html = self._r({"label": "Buy", "background_color": "transparent"})
        # transparent should not add a background-color on the outer table
        assert html.count("background-color") == 1  # only the button itself

    def test_line_height_on_anchor(self):
        # Regression: PREVIEW_RESET injects line-height:0!important on the
        # email-card td, which cascades to all descendants. Without an explicit
        # line-height on the <a>, the button text collapses and the browser's
        # default underline appears at the baseline, making it look like a
        # text-decoration bug. Every button <a> must carry line-height:1.5.
        html = self._r({"label": "Buy"})
        assert "line-height:1.5" in html

    def test_text_decoration_none_on_anchor(self):
        html = self._r({"label": "Buy", "url": "https://example.com"})
        assert "text-decoration:none" in html


# ── ColumnsRenderer ───────────────────────────────────────────────────────────

class TestColumnsRenderer:
    renderer = ColumnsRenderer()

    def _block(self, columns, **props):
        """columns is a list of {'blocks': [...]} dicts."""
        return {"type": "columns", "props": props, "columns": columns}

    def _text_child(self, content="Hello"):
        # "text" routes through RICHTEXT (RENDERER_MAP["text"] = RichTextRenderer),
        # which reads html_content — "content" is the legacy key and renders nothing.
        return {"type": "text", "props": {"html_content": content}}

    def test_empty_columns_returns_empty(self):
        assert self.renderer.render({"type": "columns", "props": {}, "columns": []}) == ""

    def test_no_columns_key_returns_empty(self):
        assert self.renderer.render({"type": "columns", "props": {}}) == ""

    def test_two_columns_renders_two_cells(self):
        block = self._block([
            {"blocks": [self._text_child("Left")]},
            {"blocks": [self._text_child("Right")]},
        ])
        html = self.renderer.render(block)
        assert "Left" in html
        assert "Right" in html
        # Cells carry the mobile-stack hook and a 50% desktop width.
        assert html.count('class="ltr-stack" width="50%"') == 2

    def test_three_columns(self):
        block = self._block([
            {"blocks": [self._text_child("A")]},
            {"blocks": [self._text_child("B")]},
            {"blocks": [self._text_child("C")]},
        ])
        html = self.renderer.render(block)
        assert html.count('class="ltr-stack" width="33%"') == 3

    def test_empty_column_renders_nbsp(self):
        block = self._block([{"blocks": []}, {"blocks": [self._text_child("X")]}])
        html = self.renderer.render(block)
        assert "&nbsp;" in html

    def test_show_dividers_adds_border(self):
        block = self._block(
            [{"blocks": []}, {"blocks": []}],
            show_dividers=True, divider_color="#cccccc",
        )
        html = self.renderer.render(block)
        assert "border-right:1px solid #cccccc" in html

    def test_background_color_applied(self):
        block = self._block([{"blocks": []}, {"blocks": []}], background_color="#f0f0f0")
        html = self.renderer.render(block)
        assert "background-color:#f0f0f0" in html

    def test_default_no_background_color(self):
        # Regression: ColumnsRenderer used to default to background-color:#ffffff,
        # which produced a white box in the email even when the canvas showed no
        # background. Transparent (no bg style) is the correct default.
        block = self._block([{"blocks": [self._text_child("A")]}, {"blocks": []}])
        html = self.renderer.render(block)
        assert "background-color" not in html

    def test_child_block_xss_safe(self):
        child = {"type": "text", "props": {"html_content": "<script>evil()</script>"}}
        block = self._block([{"blocks": [child]}, {"blocks": []}])
        html = self.renderer.render(block)
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

    def test_thumbnail_link_opens_in_new_tab(self):
        html = self._r({
            "thumbnail_url": "https://img.yt/thumb.jpg",
            "video_url": "https://youtube.com/watch?v=abc",
        })
        assert 'target="_blank"' in html

    def test_caption_link_opens_in_new_tab(self):
        html = self._r({
            "thumbnail_url": "https://img.yt/thumb.jpg",
            "video_url": "https://yt.com/v",
            "caption": "Watch the demo",
        })
        assert html.count('target="_blank"') == 2


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
                {"type": "text", "props": {"html_content": "Child text"}}
            ],
        }
        html = ContainerRenderer().render(block)
        assert "Child text" in html

    def test_row_layout_uses_table_cells(self):
        block = {
            "type": "container",
            "props": {"layout": "row"},
            "children": [
                {"type": "text", "props": {"html_content": "Left"}},
                {"type": "text", "props": {"html_content": "Right"}},
            ],
        }
        html = ContainerRenderer().render(block)
        assert "Left" in html
        assert "Right" in html
        assert "<td" in html

    def test_default_no_background_color(self):
        # Regression: ContainerRenderer used to default to background-color:#f8fafc,
        # producing a misty-blue tint in email that wasn't visible on the canvas
        # (canvas defaults to transparent). Default should emit no bg style.
        block = {
            "type": "container",
            "props": {},
            "children": [{"type": "text", "props": {"html_content": "<p>hi</p>"}}],
        }
        html = ContainerRenderer().render(block)
        assert "background-color" not in html


# ── _sanitize_rich_html ───────────────────────────────────────────────────────

class TestSanitizeRichHtml:
    def test_plain_text_is_preserved(self):
        # Text data (not inside a tag) is escaped and emitted
        out = _sanitize_rich_html("Hello & goodbye")
        assert "Hello " in out
        assert "&amp;" in out

    def test_unknown_tag_stripped_content_kept(self):
        # Unknown tag <span> is allowed; unknown tag <marquee> should drop the
        # tag itself but keep the inner text
        out = _sanitize_rich_html("<marquee>spin</marquee>")
        assert "<marquee>" not in out
        assert "spin" in out

    def test_allowed_tags_pass_through(self):
        out = _sanitize_rich_html("<p><strong>bold</strong> and <em>italic</em></p>")
        assert "<strong>bold</strong>" in out
        assert "<em>italic</em>" in out
        assert "<p>" in out

    def test_link_kept_with_safe_href(self):
        out = _sanitize_rich_html('<a href="https://frappe.io">Frappe</a>')
        assert 'href="https://frappe.io"' in out
        assert "Frappe" in out

    def test_javascript_link_sanitized(self):
        out = _sanitize_rich_html('<a href="javascript:alert(1)">click</a>')
        assert 'href="#"' in out
        assert "javascript:" not in out

    def test_ul_and_li_pass_through(self):
        out = _sanitize_rich_html("<ul><li>Item 1</li><li>Item 2</li></ul>")
        assert "<ul>" in out
        assert "<li>Item 1</li>" in out

    def test_ol_passes_through(self):
        out = _sanitize_rich_html("<ol><li>First</li></ol>")
        assert "<ol>" in out

    def test_script_tag_stripped(self):
        out = _sanitize_rich_html("<script>alert(1)</script>text")
        assert "<script>" not in out
        assert "alert" not in out

    def test_div_converted_to_br(self):
        out = _sanitize_rich_html("<div>line one</div>")
        assert "<br>" in out
        assert "<div>" not in out

    def test_style_attribute_stripped(self):
        # Inline style on a <p> should not be preserved
        out = _sanitize_rich_html('<p style="color:red">text</p>')
        assert "style=" not in out
        assert "<p>" in out

    def test_empty_string_returns_empty(self):
        assert _sanitize_rich_html("") == ""

    def test_none_like_empty_returns_empty(self):
        assert _sanitize_rich_html(None) == ""  # type: ignore[arg-type]


# ── HeaderRenderer ────────────────────────────────────────────────────────────

class TestHeaderRenderer:
    renderer = HeaderRenderer()

    def _block(self, **props):
        return {"type": "header", "props": props}

    def test_renders_logo_img(self):
        out = self.renderer.render(self._block(logo_url="https://example.com/logo.png"))
        assert '<img src="https://example.com/logo.png"' in out

    def test_placeholder_when_no_logo(self):
        out = self.renderer.render(self._block())
        assert "Logo" in out
        assert "<img" not in out

    def test_tagline_rendered(self):
        out = self.renderer.render(self._block(tagline="May 2026"))
        assert "May 2026" in out

    def test_no_tagline_no_p_tag(self):
        out = self.renderer.render(self._block(logo_url="x.png"))
        # tagline paragraph should not appear
        assert "margin:8px 0 0" not in out

    def test_background_color_applied(self):
        out = self.renderer.render(self._block(background_color="#111827"))
        assert "background-color:#111827" in out

    def test_align_center_default(self):
        out = self.renderer.render(self._block())
        assert 'align="center"' in out

    def test_border_bottom_shown_by_default(self):
        out = self.renderer.render(self._block())
        assert "border-bottom:1px solid #e5e7eb" in out

    def test_border_bottom_hidden(self):
        out = self.renderer.render(self._block(border_bottom=False))
        assert "border-bottom" not in out

    def test_logo_xss_escaped(self):
        out = self.renderer.render(self._block(logo_url='"><script>bad</script>'))
        assert "<script>" not in out


# ── RichTextRenderer ──────────────────────────────────────────────────────────

class TestRichTextRenderer:
    renderer = RichTextRenderer()

    def _block(self, html_content="", **props):
        return {"type": "rich_text", "props": {"html_content": html_content, **props}}

    def test_empty_content_returns_empty(self):
        assert self.renderer.render(self._block("")) == ""

    def test_plain_paragraph_rendered(self):
        out = self.renderer.render(self._block("<p>Hello world</p>"))
        assert "Hello world" in out
        assert "<p " in out  # p always gets a style attribute

    def test_bold_and_italic_preserved(self):
        out = self.renderer.render(self._block("<p><strong>Bold</strong> and <em>Italic</em></p>"))
        assert "<strong>Bold</strong>" in out
        assert "<em>Italic</em>" in out

    def test_link_preserved(self):
        out = self.renderer.render(self._block('<a href="https://frappe.io">Frappe</a>'))
        assert "https://frappe.io" in out
        assert "Frappe" in out

    def test_script_tag_stripped(self):
        out = self.renderer.render(self._block("<script>evil()</script><p>safe</p>"))
        assert "<script>" not in out
        assert "safe" in out

    def test_unordered_list(self):
        out = self.renderer.render(self._block("<ul><li>A</li><li>B</li></ul>"))
        assert "<ul " in out  # ul always gets a style attribute
        assert "<li>A</li>" in out

    def test_font_size_applied(self):
        out = self.renderer.render(self._block("<p>hi</p>", font_size="18px"))
        assert "font-size:18px" in out

    def test_text_color_applied(self):
        out = self.renderer.render(self._block("<p>hi</p>", text_color="#ff0000"))
        assert "color:#ff0000" in out

    def test_padding_applied(self):
        out = self.renderer.render(self._block("<p>hi</p>", padding_top=10, padding_right=20, padding_bottom=10, padding_left=20))
        assert "padding:10px 20px 10px 20px" in out

    def test_output_is_email_table(self):
        out = self.renderer.render(self._block("<p>hi</p>"))
        assert "<table" in out
        assert 'width="100%"' in out

    def test_background_color_applied_to_outer_table(self):
        # Regression: rich_text blocks used to silently ignore background_color —
        # the canvas showed the tinted section but the compiled email was always
        # white. The outer <table> must carry the background-color so the email
        # matches the canvas.
        out = self.renderer.render(self._block("<p>hi</p>", background_color="#F5F7F2"))
        assert "background-color:#F5F7F2" in out

    def test_no_background_color_when_transparent(self):
        out = self.renderer.render(self._block("<p>hi</p>", background_color="transparent"))
        assert "background-color:transparent" not in out

    def test_last_paragraph_has_zero_bottom_margin(self):
        # The last <p> must have margin:0 so it doesn't add trailing space beyond
        # the block's padding_bottom (which may be 0).
        out = self.renderer.render(self._block("<p>Only paragraph</p>"))
        # The single paragraph is also the last one — must end with margin:0.
        assert 'margin:0;' in out

    def test_middle_paragraphs_have_bottom_margin(self):
        # Only the last <p> should lose its bottom margin; earlier ones keep it.
        out = self.renderer.render(self._block("<p>First</p><p>Last</p>"))
        assert "margin:0 0 0.75em 0;" in out   # first paragraph keeps spacing
        assert "margin:0;" in out               # last paragraph gets zero

    def test_single_paragraph_no_trailing_space(self):
        # When there is only one paragraph and padding_bottom is 0, the rendered
        # output must NOT contain a non-zero bottom margin on the <p>.
        out = self.renderer.render(self._block("<p>Hello</p>", padding_bottom=0))
        assert "margin:0 0 0.75em" not in out

    def test_ordered_list_has_inside_positioning(self):
        # list-style-position:inside keeps numbers next to text regardless of
        # the block's text-align. Outside positioning (the browser default) places
        # the marker in the padding area, which looks broken when text is centered.
        out = self.renderer.render(self._block("<ol><li>apples</li><li>peaches</li></ol>"))
        assert "list-style-position:inside" in out
        assert "padding-left:0" in out

    def test_unordered_list_has_inside_positioning(self):
        out = self.renderer.render(self._block("<ul><li>A</li><li>B</li></ul>"))
        assert "list-style-position:inside" in out
        assert "padding-left:0" in out


# ── ImageRenderer link-through ────────────────────────────────────────────────

class TestImageRendererLinkThrough:
    renderer = ImageRenderer()

    def _block(self, **props):
        return {"type": "image", "props": {"image_url": "https://example.com/img.png", **props}}

    def test_no_link_url_no_anchor(self):
        out = self.renderer.render(self._block())
        assert "<a " not in out

    def test_link_url_wraps_image(self):
        out = self.renderer.render(self._block(link_url="https://frappe.io"))
        assert '<a href="https://frappe.io"' in out

    def test_link_url_javascript_blocked(self):
        # _safe_url converts dangerous URLs to "#"; the renderer then skips
        # the anchor entirely (treats "#" the same as no link)
        out = self.renderer.render(self._block(link_url="javascript:evil()"))
        assert "javascript:" not in out
        # No <a> wrapper should appear
        assert "<a " not in out


# ── LinkListRenderer ─────────────────────────────────────────────────────────

class TestLinkListRenderer:
    renderer = LinkListRenderer()

    def _block(self, items=None, **props):
        return {"type": "link_list", "props": {"items": items or [], **props}}

    def _item(self, title="Title", url="https://example.com", description="Desc"):
        return {"title": title, "url": url, "description": description}

    def test_empty_items_returns_empty(self):
        assert self.renderer.render(self._block()) == ""

    def test_item_title_rendered(self):
        out = self.renderer.render(self._block([self._item("My Article")]))
        assert "My Article" in out

    def test_item_link_rendered(self):
        out = self.renderer.render(self._block([self._item(url="https://frappe.io")]))
        assert 'href="https://frappe.io"' in out

    def test_javascript_url_blocked(self):
        out = self.renderer.render(self._block([self._item(url="javascript:evil()")]))
        assert "javascript:" not in out

    def test_description_rendered(self):
        out = self.renderer.render(self._block([self._item(description="A great read about Frappe.")]))
        assert "A great read about Frappe." in out

    def test_no_description_no_desc_tag(self):
        item = {"title": "Title", "url": "https://example.com"}  # no description key
        out = self.renderer.render(self._block([item]))
        assert "Title" in out

    def test_bullet_marker(self):
        out = self.renderer.render(self._block([self._item()], style="bullet"))
        assert "&bull;" in out

    def test_numbered_marker(self):
        out = self.renderer.render(self._block(
            [self._item("A"), self._item("B")], style="numbered"
        ))
        assert "1." in out
        assert "2." in out

    def test_no_marker_style_none(self):
        out = self.renderer.render(self._block([self._item()], style="none"))
        assert "&bull;" not in out

    def test_heading_rendered(self):
        out = self.renderer.render(self._block([self._item()], heading="Fresh Reads"))
        assert "Fresh Reads" in out

    def test_xss_title_escaped(self):
        out = self.renderer.render(self._block([self._item(title="<script>bad</script>")]))
        assert "<script>" not in out

    def test_multiple_items(self):
        out = self.renderer.render(self._block([
            self._item("Article One"),
            self._item("Article Two"),
            self._item("Article Three"),
        ]))
        assert "Article One" in out
        assert "Article Three" in out

    def test_link_color_applied(self):
        out = self.renderer.render(self._block([self._item()], link_color="#ff0000"))
        assert "color:#ff0000" in out

    def test_output_is_email_table(self):
        out = self.renderer.render(self._block([self._item()]))
        assert "<table" in out
        assert 'width="100%"' in out


# ── RENDERER_MAP completeness ─────────────────────────────────────────────────

class TestRendererMap:
    EXPECTED_TYPES = {
        "hero", "text", "image", "image_text", "button", "columns",
        "container", "section_label", "divider", "footer", "spacer",
        "quote", "social", "product_card", "video_thumb",
        "header", "rich_text", "link_list",
    }

    def test_all_expected_types_present(self):
        assert self.EXPECTED_TYPES == set(RENDERER_MAP.keys())

    def test_all_renderers_have_render_method(self):
        for name, renderer in RENDERER_MAP.items():
            assert hasattr(renderer, "render"), f"{name} renderer missing .render()"


# ── Font selection ────────────────────────────────────────────────────────────

from letters.letters.utils.fonts import FONT_STACKS, font_stack


class TestFontStack:
    def test_known_name_resolves_to_full_stack(self):
        assert font_stack({"font_family": "Verdana"}, "FB") == "Verdana, Geneva, sans-serif"

    def test_name_is_trimmed(self):
        assert font_stack({"font_family": "  Georgia  "}, "FB") == FONT_STACKS["Georgia"]

    def test_empty_returns_fallback(self):
        assert font_stack({"font_family": ""}, "FB") == "FB"
        assert font_stack({}, "FB") == "FB"

    def test_unknown_name_returns_fallback(self):
        # Anything outside the safe-font whitelist falls through to the caller's
        # default; the raw value is never echoed into the output.
        assert font_stack({"font_family": "UnknownFont"}, "FB") == "FB"
        assert font_stack({"font_family": "<script>"}, "FB") == "FB"
        # Known fonts must NOT return the fallback
        assert font_stack({"font_family": "Comic Sans MS"}, "FB") != "FB"

    def test_every_option_has_a_generic_fallback(self):
        # Comic Sans uses 'cursive' as its generic family — include it alongside
        # the standard email-safe generic families.
        for stack in FONT_STACKS.values():
            assert stack.rstrip().endswith(("sans-serif", "serif", "monospace", "cursive"))


class TestFontInRenderers:
    def test_text_uses_chosen_font(self):
        html = RichTextRenderer().render(
            {"type": "text", "props": {"html_content": "hi", "font_family": "Verdana"}}
        )
        assert "font-family:Verdana, Geneva, sans-serif;" in html

    def test_text_without_font_keeps_default(self):
        html = RichTextRenderer().render({"type": "text", "props": {"html_content": "hi"}})
        assert "font-family:Arial,sans-serif;" in html

    def test_hero_applies_one_font_to_both_lines(self):
        html = HeroRenderer().render(
            {"type": "hero", "props": {"heading": "H", "subheading": "S", "font_family": "Tahoma"}}
        )
        # Both the heading and subheading pick up the chosen face.
        assert html.count("Tahoma, Geneva, sans-serif") == 2

    def test_hero_without_font_keeps_serif_heading_sans_subheading(self):
        html = HeroRenderer().render(
            {"type": "hero", "props": {"heading": "H", "subheading": "S"}}
        )
        assert "font-family:Georgia,'Times New Roman',serif;" in html
        assert "font-family:Arial,sans-serif;" in html

    def test_button_uses_chosen_font(self):
        html = ButtonRenderer().render(
            {"type": "button", "props": {"label": "Go", "font_family": "Courier New"}}
        )
        assert "'Courier New', Courier, monospace" in html


# ── _sanitize_rich_html — suppressed-tag nesting, void tags ──────────────────

class TestSanitizeRichHtml:
    def test_script_tags_and_content_are_stripped(self):
        result = _sanitize_rich_html('<p>Hello</p><script>alert(1)</script><p>World</p>')
        assert "<script" not in result
        assert "alert" not in result
        assert "Hello" in result
        assert "World" in result

    def test_nested_script_does_not_leak_inner_tags(self):
        # Depth > 1: inner tags inside a suppressed block must still be suppressed.
        result = _sanitize_rich_html('<script><b>inner</b>txt</script>after')
        assert "<b>" not in result
        assert "inner" not in result
        assert "after" in result

    def test_void_tags_self_closed(self):
        result = _sanitize_rich_html('<p>line1<br>line2</p>')
        assert '<br />' in result

    def test_entity_ref_preserved(self):
        result = _sanitize_rich_html('<p>&amp;</p>')
        assert '&amp;' in result

    def test_char_ref_preserved(self):
        result = _sanitize_rich_html('<p>&#169;</p>')
        assert '&#169;' in result

    def test_div_converted_to_br(self):
        result = _sanitize_rich_html('<div>line</div>')
        assert '<br>' in result


# ── _safe_url — get_url path with mock ───────────────────────────────────────

class TestSafeUrlWithGetUrl:
    def test_absolute_path_left_relative_outside_frappe_runtime(self):
        # In a test environment frappe is a MagicMock, not a real package, so
        # `from frappe.utils import get_url` raises ModuleNotFoundError. _safe_url
        # catches that and returns the path unchanged (the fallback branch).
        # The production path (get_url prefixes the site host) is exercised only
        # inside a running Frappe bench — verified manually on letters.localhost.
        result = _safe_url("/files/img.png")
        assert result == "/files/img.png"


# ── ContainerRenderer — stacked layout with gap row ─────────────────────────

class TestContainerStackedLayout:
    def test_gap_row_inserted_between_children_in_stacked_layout(self):
        block = {
            "type": "container",
            "props": {"layout": "column", "gap": 16},
            "children": [
                {"type": "text", "props": {"html_content": "<p>A</p>"}},
                {"type": "text", "props": {"html_content": "<p>B</p>"}},
            ],
        }
        html = ContainerRenderer().render(block)
        # A spacer row (height:16px) must appear between the two content rows.
        assert "height:16px" in html

    def test_no_gap_row_when_gap_is_zero(self):
        block = {
            "type": "container",
            "props": {"layout": "column", "gap": 0},
            "children": [
                {"type": "text", "props": {"html_content": "<p>A</p>"}},
                {"type": "text", "props": {"html_content": "<p>B</p>"}},
            ],
        }
        html = ContainerRenderer().render(block)
        assert "height:0px" not in html

    def test_last_child_has_no_right_pad(self):
        block = {
            "type": "container",
            "props": {"layout": "row", "gap": 20},
            "children": [
                {"type": "text", "props": {"html_content": "L"}},
                {"type": "text", "props": {"html_content": "R"}},
            ],
        }
        html = ContainerRenderer().render(block)
        # Last cell: right_pad=0, left_pad=half_gap=10.
        assert "padding:0 0px 0 10px" in html


# ── ProductCardRenderer ───────────────────────────────────────────────────────

class TestProductCardRenderer:
    def test_renders_title_and_price(self):
        html = ProductCardRenderer().render({
            "type": "product_card",
            "props": {"title": "Widget", "price": "$9.99"},
        })
        assert "Widget" in html
        assert "$9.99" in html

    def test_button_absent_when_no_label(self):
        html = ProductCardRenderer().render({
            "type": "product_card",
            "props": {"title": "Widget", "button_label": "", "button_url": "#"},
        })
        # No button anchor when label is empty.
        assert "display:inline-block" not in html

    def test_image_absent_when_no_url(self):
        html = ProductCardRenderer().render({
            "type": "product_card",
            "props": {"title": "Widget", "image_url": ""},
        })
        assert "<img" not in html


# ── ImageTextRenderer padding ─────────────────────────────────────────────────

def _image_text_block(position="left", pl=32, pr=32, pt=20, pb=20):
    return {
        "type": "image_text",
        "props": {
            "image_url": "https://example.com/img.jpg",
            "text": "Hello",
            "image_position": position,
            "layout_mode": "side",
            "padding_left": pl, "padding_right": pr,
            "padding_top": pt, "padding_bottom": pb,
        },
    }


class TestImageTextRendererPadding:
    """Block padding goes on the outer wrapper; inner cells carry only the gap."""

    def test_block_padding_on_outer_wrapper(self):
        # All block padding should appear on the outer <td>, not distributed to inner cells
        html = ImageTextRenderer().render(_image_text_block(position="left", pl=40, pr=24))
        # Outer wrapper td is the first <td with style containing the full padding
        assert "padding:20px 24px 20px 40px" in html

    def test_img_cell_has_only_gap_not_block_padding(self):
        # Image cell should have only the gap padding, not the block's outer padding
        html = ImageTextRenderer().render(_image_text_block(position="left", pl=40, pr=24))
        tds = html.split("<td")
        img_td = next(t for t in tds if "img.jpg" in t)
        assert "40px" not in img_td, "block pl should not appear in image cell"
        assert "24px" not in img_td, "block pr should not appear in image cell"

    def test_text_cell_has_only_gap_not_block_padding(self):
        html = ImageTextRenderer().render(_image_text_block(position="left", pl=40, pr=24))
        tds = html.split("<td")
        text_td = next(t for t in tds if "Hello" in t)
        assert "40px" not in text_td, "block pl should not appear in text cell"
        assert "24px" not in text_td, "block pr should not appear in text cell"

    def test_position_right_outer_wrapper_has_block_padding(self):
        html = ImageTextRenderer().render(_image_text_block(position="right", pl=40, pr=24))
        assert "padding:20px 24px 20px 40px" in html

    def test_position_left_column_order(self):
        html = ImageTextRenderer().render(_image_text_block(position="left"))
        assert html.index("img.jpg") < html.index("Hello")

    def test_position_right_column_order(self):
        html = ImageTextRenderer().render(_image_text_block(position="right"))
        assert html.index("Hello") < html.index("img.jpg")


# ── Mobile responsiveness ─────────────────────────────────────────────────────

from letters.letters.utils.block_renderers import _font_scale_class, _aspect_ref_width
from letters.letters.utils.email_compiler import EmailCompiler


class TestFontScaleClass:
    def test_large_size_gets_xl(self):
        assert _font_scale_class("40px") == "ltr-fs-xl"
        assert _font_scale_class("32px") == "ltr-fs-xl"

    def test_medium_size_gets_lg(self):
        assert _font_scale_class("28px") == "ltr-fs-lg"
        assert _font_scale_class("24px") == "ltr-fs-lg"

    def test_body_size_gets_nothing(self):
        assert _font_scale_class("16px") == ""
        assert _font_scale_class("23px") == ""

    def test_garbage_size_is_safe(self):
        assert _font_scale_class("") == ""
        assert _font_scale_class("auto") == ""
        assert _font_scale_class(None) == ""


class TestAspectRefWidth:
    def test_pixel_width_used_directly(self):
        assert _aspect_ref_width("320px") == 320

    def test_percent_resolved_against_body(self):
        assert _aspect_ref_width("100%") == 600
        assert _aspect_ref_width("90%") == 540

    def test_auto_falls_back_to_body(self):
        assert _aspect_ref_width("auto") == 600
        assert _aspect_ref_width("") == 600


class TestImageResponsiveHeight:
    def _r(self, props):
        props = {"image_url": "https://x.com/a.png", **props}
        return ImageRenderer().render({"type": "image", "props": props})

    def test_cover_uses_aspect_ratio_not_frozen_height(self):
        html = self._r({
            "image_width": "100%", "image_height": "300px", "image_fit": "cover",
            "padding_left": 0, "padding_right": 0,
        })
        assert "aspect-ratio:600/300" in html
        assert "height:auto" in html
        assert "height:300px" not in html  # no frozen height that would crop on mobile

    def test_cover_keeps_focus_point(self):
        html = self._r({
            "image_width": "100%", "image_height": "300px",
            "image_fit": "cover", "object_position": "50% 72%",
        })
        assert "object-position:50% 72%" in html

    def test_contain_keeps_fixed_height(self):
        # Logos use contain and must not be re-shaped by aspect-ratio.
        html = self._r({"image_width": "auto", "image_height": "32px", "image_fit": "contain"})
        assert "height:32px" in html
        assert "aspect-ratio" not in html

    def test_cover_aspect_ratio_uses_nested_column_width_not_full_email(self):
        # An image inside a 2-up row column is ~300px wide, not the full
        # 600px email body — the aspect-ratio must be computed against its
        # actual rendered width or object-fit:cover over-crops it.
        html = ContainerRenderer().render({
            "type": "container",
            "props": {"layout": "row", "gap": 0, "padding_left": 0, "padding_right": 0},
            "children": [
                {"type": "image", "props": {
                    "image_url": "https://x.com/a.png",
                    "image_width": "100%", "image_height": "130px", "image_fit": "cover",
                    "padding_left": 0, "padding_right": 0,
                }},
                {"type": "image", "props": {
                    "image_url": "https://x.com/b.png",
                    "image_width": "100%", "image_height": "130px", "image_fit": "cover",
                    "padding_left": 0, "padding_right": 0,
                }},
            ],
        })
        assert html.count("aspect-ratio:300/130") == 2
        assert "aspect-ratio:600/130" not in html


class TestContainerRowStacks:
    def _row(self, children):
        return ContainerRenderer().render(
            {"type": "container", "props": {"layout": "row"}, "children": children}
        )

    def test_row_cells_carry_stack_hook(self):
        html = self._row([
            {"type": "text", "props": {"html_content": "<p>A</p>"}},
            {"type": "text", "props": {"html_content": "<p>B</p>"}},
        ])
        assert html.count('class="ltr-stack"') == 2

    def test_four_or_more_equal_columns_get_2up_grid(self):
        html = ContainerRenderer().render({
            "type": "container",
            "props": {"layout": "row", "gap": 0},
            "children": [{"type": "text", "props": {"html_content": f"<p>{i}</p>"}} for i in range(5)],
        })
        assert html.count('class="ltr-stack-2"') == 5
        assert 'class="ltr-stack"' not in html

    def test_price_and_button_row_auto_opts_out_of_stacking(self):
        html = self._row([
            {"type": "text", "props": {"html_content": "<p>$54</p>"}},
            {"type": "button", "props": {"label": "Shop Now"}},
        ])
        assert "ltr-stack" not in html

    def test_mobile_stack_false_opts_out_of_stacking(self):
        stacks_html = self._row([
            {"type": "text", "props": {"html_content": "<p>A</p>"}},
            {"type": "text", "props": {"html_content": "<p>B</p>"}},
        ])
        no_stack_html = ContainerRenderer().render({
            "type": "container",
            "props": {"layout": "row", "mobile_stack": False},
            "children": [
                {"type": "text", "props": {"html_content": "<p>A</p>"}},
                {"type": "text", "props": {"html_content": "<p>B</p>"}},
            ],
        })
        assert "ltr-stack" in stacks_html
        assert "ltr-stack" not in no_stack_html

    def test_mobile_stack_true_forces_stacking_for_price_button_row(self):
        html = ContainerRenderer().render({
            "type": "container",
            "props": {"layout": "row", "mobile_stack": True},
            "children": [
                {"type": "text", "props": {"html_content": "<p>$54</p>"}},
                {"type": "button", "props": {"label": "Shop Now"}},
            ],
        })
        assert "ltr-stack" in html

    def test_vertical_dividers_dont_steal_column_width(self):
        html = ContainerRenderer().render({
            "type": "container",
            "props": {"layout": "row"},
            "children": [
                {"type": "text", "props": {"html_content": "<p>A</p>"}},
                {"type": "divider", "props": {"orientation": "vertical"}},
                {"type": "text", "props": {"html_content": "<p>B</p>"}},
                {"type": "divider", "props": {"orientation": "vertical"}},
                {"type": "text", "props": {"html_content": "<p>C</p>"}},
            ],
        })
        assert html.count('width="33%"') == 3
        assert html.count('width="24px"') == 2

    def test_vertical_dividers_get_flatten_hook_when_stacking(self):
        html = ContainerRenderer().render({
            "type": "container",
            "props": {"layout": "row"},
            "children": [
                {"type": "text", "props": {"html_content": "<p>A</p>"}},
                {"type": "divider", "props": {"orientation": "vertical"}},
                {"type": "text", "props": {"html_content": "<p>B</p>"}},
            ],
        })
        assert 'class="ltr-vdivider"' in html
        assert "ltr-stack" in html  # content cells still stack normally

    def test_vertical_dividers_excluded_from_2up_grid_threshold(self):
        # 3 real content cells + 2 dividers shouldn't trip the >=4 stat-row
        # heuristic (that's for 4+ actual content items, not divider count).
        html = ContainerRenderer().render({
            "type": "container",
            "props": {"layout": "row"},
            "children": [
                {"type": "text", "props": {"html_content": "<p>A</p>"}},
                {"type": "divider", "props": {"orientation": "vertical"}},
                {"type": "text", "props": {"html_content": "<p>B</p>"}},
                {"type": "divider", "props": {"orientation": "vertical"}},
                {"type": "text", "props": {"html_content": "<p>C</p>"}},
            ],
        })
        assert "ltr-stack-2" not in html

    def test_wide_padding_gets_pad_hook(self):
        html = ContainerRenderer().render({
            "type": "container",
            "props": {"layout": "column", "padding_left": 40, "padding_right": 40},
            "children": [{"type": "text", "props": {"html_content": "<p>Hi</p>"}}],
        })
        assert "ltr-pad-x" in html

    def test_narrow_padding_no_pad_hook(self):
        html = ContainerRenderer().render({
            "type": "container",
            "props": {"layout": "column", "padding_left": 16, "padding_right": 16},
            "children": [{"type": "text", "props": {"html_content": "<p>Hi</p>"}}],
        })
        assert "ltr-pad-x" not in html


class TestWideSidePaddingTrims:
    """Wide horizontal padding gets the mobile-trim hook on every block, not just
    containers (a text/button/social block at 40px each side crowds a phone)."""

    def test_text_block_wide_padding(self):
        html = RichTextRenderer().render({"type": "text", "props": {
            "html_content": "<p>Hi</p>", "padding_left": 40, "padding_right": 40}})
        assert "ltr-pad-x" in html

    def test_button_wide_padding(self):
        html = ButtonRenderer().render({"type": "button", "props": {
            "label": "Go", "padding_left": 40, "padding_right": 40}})
        assert "ltr-pad-x" in html

    def test_image_wide_padding(self):
        html = ImageRenderer().render({"type": "image", "props": {
            "image_url": "https://x.com/a.png", "padding_left": 40, "padding_right": 40}})
        assert "ltr-pad-x" in html

    def test_narrow_padding_no_hook(self):
        html = RichTextRenderer().render({"type": "text", "props": {
            "html_content": "<p>Hi</p>", "padding_left": 16, "padding_right": 16}})
        assert "ltr-pad-x" not in html

    def test_font_and_pad_hooks_merge_on_one_cell(self):
        # A big heading with wide padding must carry both hooks in one class attr.
        html = RichTextRenderer().render({"type": "text", "props": {
            "html_content": "<p>Big</p>", "font_size": "34px",
            "padding_left": 40, "padding_right": 40}})
        assert 'class="ltr-fs-xl ltr-pad-x"' in html

    def test_wide_horizontal_spacing_trims(self):
        # _spacing_wrapper (block spacing, not padding) also trims wide L/R spacing.
        html = ButtonRenderer().render({"type": "button", "props": {
            "label": "Go", "spacing_left": 40, "spacing_right": 40}})
        assert "ltr-pad-x" in html


class TestCompilerMobileStyle:
    def test_wrapper_includes_media_query(self):
        html = EmailCompiler("[]").compile()
        assert "@media only screen and (max-width:600px)" in html
        assert ".ltr-stack" in html
        assert ".ltr-fs-xl" in html

    def test_large_text_block_gets_scale_hook(self):
        blocks = '[{"type":"text","props":{"html_content":"<p>Big</p>","font_size":"34px"}}]'
        html = EmailCompiler(blocks).compile()
        assert "ltr-fs-xl" in html

    def test_body_text_block_gets_no_scale_hook(self):
        blocks = '[{"type":"text","props":{"html_content":"<p>Body</p>","font_size":"16px"}}]'
        html = EmailCompiler(blocks).compile()
        # class attr only, not the media-query rule name in the <style> block
        assert 'class="ltr-fs' not in html
