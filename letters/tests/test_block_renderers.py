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
    _hex_to_rgba,
    _padding,
    _spacing_wrapper,
    _sanitize_rich_html,
    HeroRenderer,
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
        assert html.count('<td width="50%"') == 2

    def test_three_columns(self):
        block = self._block([
            {"blocks": [self._text_child("A")]},
            {"blocks": [self._text_child("B")]},
            {"blocks": [self._text_child("C")]},
        ])
        html = self.renderer.render(block)
        assert html.count('<td width="33%"') == 3

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
        assert "<p>" in out

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
        assert "<ul>" in out
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
        assert font_stack({"font_family": "Comic Sans MS"}, "FB") == "FB"
        assert font_stack({"font_family": "<script>"}, "FB") == "FB"

    def test_every_option_has_a_generic_fallback(self):
        for stack in FONT_STACKS.values():
            assert stack.rstrip().endswith(("sans-serif", "serif", "monospace"))


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
