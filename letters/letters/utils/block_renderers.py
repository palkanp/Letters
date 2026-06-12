from abc import ABC, abstractmethod
from base64 import b64encode
from html import escape
from html.parser import HTMLParser
from typing import Any, List, Optional, Tuple
import re

from letters.letters.utils.fonts import font_stack


def _safe_url(url: str) -> str:
    """Return an HTML-escaped URL, rejecting dangerous protocol schemes."""
    url = (url or "").strip()
    if url.lower().lstrip("\x00\t\n\r\f ").startswith(("javascript:", "data:", "vbscript:")):
        return "#"
    return escape(url)


def _abs_image_src(url: str) -> str:
    """Make an image src absolute and HTML-escape it.

    Uploaded files are stored as site-relative paths like "/files/x.png". Email
    clients have no base URL to resolve those against, so a relative src always
    renders as a broken image in the inbox. Prepend the site's public URL so the
    image loads. Already-absolute (http/https/protocol-relative/data) URLs and
    empty values are left untouched.
    """
    url = (url or "").strip()
    if not url or url.startswith(("http://", "https://", "//", "data:")):
        return escape(url)
    if url.startswith("/"):
        try:
            from frappe.utils import get_url
            return escape(get_url(url))
        except Exception:
            # Outside a Frappe runtime (e.g. unit tests) leave it relative.
            return escape(url)
    return escape(url)


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert a #RRGGBB hex string to an rgba() value safe for all email clients."""
    hex_color = hex_color.strip().lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    if len(hex_color) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", hex_color):
        return f"rgba(0,0,0,{alpha})"
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _padding(props: dict, dt: int = 20, dr: int = 16, db: int = 20, dl: int = 16) -> str:
    """Return a CSS padding shorthand from block props, falling back to supplied defaults."""
    t = int(props.get("padding_top",    dt))
    r = int(props.get("padding_right",  dr))
    b = int(props.get("padding_bottom", db))
    l = int(props.get("padding_left",   dl))
    return f"{t}px {r}px {b}px {l}px"


def _spacing_wrapper(inner_html: str, props: dict) -> str:
    """Wrap a block's HTML in a table row that applies spacing_top / spacing_bottom."""
    top    = int(props.get("spacing_top", 0))
    bottom = int(props.get("spacing_bottom", 0))
    if top == 0 and bottom == 0:
        return inner_html
    return (
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
        f'<tr><td style="padding-top:{top}px;padding-bottom:{bottom}px;">'
        f'{inner_html}'
        f'</td></tr></table>'
    )


# ── Rich-text HTML sanitizer ─────────────────────────────────────────────────

_RT_ALLOWED = frozenset({
    "p", "br", "strong", "b", "em", "i", "u", "a", "ul", "ol", "li", "span",
    "s", "del",
})
_RT_BLOCK_TO_BR = frozenset({
    "div", "h1", "h2", "h3", "h4", "h5", "h6",
})
_RT_VOID = frozenset({"br"})
# Tags that must be rendered as styled spans for email-client compatibility
_RT_STYLED_SPAN = {
    "s": 'text-decoration:line-through;',
    "del": 'text-decoration:line-through;',
}
# Tags whose inner content is entirely suppressed (dangerous)
_RT_SUPPRESS = frozenset({"script", "style", "head", "meta", "link", "iframe", "object", "embed"})


class _RichTextSanitizer(HTMLParser):
    """Parse arbitrary HTML and emit only whitelisted tags/attributes.

    Content inside dangerous tags (script, style, etc.) is suppressed entirely.
    Unknown tags are stripped but their text content is preserved.
    Block-level containers (div, headings) are converted to <br>.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self._out: List[str] = []
        self._suppress_depth: int = 0  # >0 means we're inside a dangerous tag

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag in _RT_SUPPRESS:
            self._suppress_depth += 1
            return
        if self._suppress_depth > 0:
            return
        if tag in _RT_ALLOWED:
            if tag == "a":
                href = dict(attrs).get("href") or ""
                safe = _safe_url(href)
                self._out.append(
                    f'<a href="{safe}" style="color:#2563eb;" target="_blank">'
                )
            elif tag in _RT_STYLED_SPAN:
                self._out.append(f'<span style="{_RT_STYLED_SPAN[tag]}">')
            elif tag in _RT_VOID:
                self._out.append(f"<{tag} />")
            else:
                self._out.append(f"<{tag}>")
        elif tag in _RT_BLOCK_TO_BR:
            # Convert block-level wrappers (div, headings) to line breaks
            self._out.append("<br>")

    def handle_endtag(self, tag: str) -> None:
        if tag in _RT_SUPPRESS:
            self._suppress_depth = max(0, self._suppress_depth - 1)
            return
        if self._suppress_depth > 0:
            return
        if tag in _RT_ALLOWED and tag not in _RT_VOID:
            if tag in _RT_STYLED_SPAN:
                self._out.append("</span>")
            else:
                self._out.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if self._suppress_depth == 0:
            self._out.append(escape(data))

    def handle_entityref(self, name: str) -> None:  # type: ignore[override]
        if self._suppress_depth == 0:
            self._out.append(f"&{name};")

    def handle_charref(self, name: str) -> None:  # type: ignore[override]
        if self._suppress_depth == 0:
            self._out.append(f"&#{name};")

    def get_output(self) -> str:
        return "".join(self._out)




def _sanitize_rich_html(html_str: str) -> str:
    """Whitelist-sanitize rich-text HTML for safe email output."""
    sanitizer = _RichTextSanitizer()
    sanitizer.feed(html_str or "")
    return sanitizer.get_output()


class BlockRenderer(ABC):
    @abstractmethod
    def render(self, block: dict[str, Any]) -> str:
        """Return email-safe HTML for this block."""


class HeroRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        bg              = escape(p.get("background_color", "#ffffff"))
        heading         = escape(p.get("heading", ""))
        subheading      = escape(p.get("subheading", ""))
        heading_color   = escape(p.get("heading_color", "#111827"))
        heading_size    = escape(p.get("heading_size", "30px"))
        subheading_color = escape(p.get("subheading_color", "#6b7280"))
        text_align      = escape(p.get("text_align", "center"))
        heading_font    = font_stack(p, "Georgia,'Times New Roman',serif")
        subheading_font = font_stack(p, "Arial,sans-serif")
        padding         = _padding(p, 40, 16, 40, 16)

        heading_html = (
            f'<h1 style="margin:0 0 12px;font-family:{heading_font};'
            f'font-size:{heading_size};font-weight:bold;color:{heading_color};'
            f'line-height:1.2;text-align:{text_align};">{heading}</h1>'
        ) if heading else ""
        subheading_html = (
            f'<p style="margin:0;font-family:{subheading_font};font-size:16px;'
            f'color:{subheading_color};line-height:1.5;text-align:{text_align};">{subheading}</p>'
        ) if subheading else ""

        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background-color:{bg};">'
            f'<tr><td align="{text_align}" style="padding:{padding};">'
            f'{heading_html}{subheading_html}'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class ImageRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        image_url     = _abs_image_src(p.get("image_url", ""))
        caption       = escape(p.get("caption", ""))
        alt           = escape(p.get("alt", ""))
        bg            = escape(p.get("background_color", "#ffffff"))
        border        = escape(p.get("border", "0.5px solid #383838"))
        border_radius = escape(p.get("border_radius", "0"))
        caption_color = escape(p.get("caption_color", "#9ca3af"))

        border_style = f"border:{border};" if border and border != "none" else ""
        radius_style = f"border-radius:{border_radius};" if border_radius and border_radius != "0" else ""

        if not image_url:
            return ""  # Don't render empty image blocks

        link_url = _safe_url(p.get("link_url", ""))

        img_tag = (
            f'<img src="{image_url}" width="100%" alt="{alt}"'
            f' style="display:block;max-width:100%;height:auto;{border_style}{radius_style}" />'
        )
        # Wrap image in a clickable link when link_url is set
        img_content = (
            f'<a href="{link_url}" style="display:block;text-decoration:none;">{img_tag}</a>'
            if link_url and link_url != "#"
            else img_tag
        )

        caption_html = ""
        if caption:
            caption_html = (
                f'<tr><td style="padding:6px 32px 0;font-family:Arial,sans-serif;'
                f'font-size:12px;color:{caption_color};line-height:1.4;">{caption}</td></tr>'
            )

        padding = _padding(p, 16, 16, 16, 16)
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background-color:{bg};">'
            f'<tr><td style="padding:{padding};">'
            f'{img_content}'
            f'</td></tr>'
            f'{caption_html}'
            f'</table>'
        )
        return _spacing_wrapper(html, p)


class SectionLabelRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        label         = escape(p.get("label", ""))
        text_color    = escape(p.get("text_color", "#383838"))
        line_color    = escape(p.get("line_color", "#ededed"))
        line_position = p.get("line_position", "below")
        align         = escape(p.get("align", "left"))
        font_size     = escape(p.get("font_size", "11px"))
        font_weight   = escape(str(p.get("font_weight", "600")))
        font          = font_stack(p, "Arial,sans-serif")

        line_html = f'<hr style="border:0;border-top:1px solid {line_color};margin:8px 0 0;" />'
        above_line = line_html if line_position == "above" else ""
        below_line = line_html if line_position in ("below", "") or not line_position else ""

        padding = _padding(p, 12, 16, 12, 16)
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr><td style="padding:{padding};" align="{align}">'
            f'{above_line}'
            f'<span style="font-family:{font};font-size:{font_size};font-weight:{font_weight};'
            f'color:{text_color};text-transform:uppercase;letter-spacing:1px;'
            f'line-height:1.2;">{label}</span>'
            f'{below_line}'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class ImageTextRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        image_url   = _abs_image_src(p.get("image_url", ""))
        text        = escape(p.get("text", ""))
        position    = p.get("image_position", "left")
        img_width   = p.get("image_width", "160px")
        layout_mode = p.get("layout_mode", "side")
        font        = font_stack(p, "Arial,sans-serif")

        img_px = img_width.replace("px", "") if img_width.endswith("px") else "160"

        pt = int(p.get("padding_top",    20))
        pr = int(p.get("padding_right",  32))
        pb = int(p.get("padding_bottom", 20))
        pl = int(p.get("padding_left",   32))

        if layout_mode == "wrap":
            # Float pattern: image aligned left/right, text flows around it
            # Email clients handle align="left"/"right" on the image's containing cell
            margin_left  = "0" if position == "left"  else "16px"
            margin_right = "16px" if position == "left" else "0"
            align_attr   = "left" if position == "left" else "right"
            img_html = (
                f'<img src="{image_url}" width="{img_px}" align="{align_attr}"'
                f' style="display:inline;border:0;margin-left:{margin_left};'
                f'margin-right:{margin_right};margin-bottom:8px;" alt="" />'
            ) if image_url else ""
            html = (
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
                f'<tr><td style="padding:{pt}px {pr}px {pb}px {pl}px;">'
                f'{img_html}'
                f'<p style="margin:0;font-family:{font};font-size:15px;'
                f'color:#333333;line-height:1.6;">{text}</p>'
                f'</td></tr></table>'
            )
        else:
            # Side-by-side (default)
            gap = 8
            img_cell = (
                f'<td width="{img_px}" valign="top" style="padding:{pt}px {gap}px {pb}px {pl}px;">'
                f'<img src="{image_url}" width="{img_px}" style="display:block;border:0;" alt="" />'
                f'</td>'
            ) if image_url else (
                f'<td width="{img_px}" valign="top" style="padding:{pt}px {gap}px {pb}px {pl}px;">'
                f'<div style="width:{img_px}px;height:100px;background:#eeeeee;'
                f'font-family:Arial,sans-serif;font-size:12px;color:#999;text-align:center;'
                f'padding-top:40px;">Image</div>'
                f'</td>'
            )
            text_cell = (
                f'<td valign="top" style="padding:{pt}px {pr}px {pb}px {gap}px;">'
                f'<p style="margin:0;font-family:{font};font-size:15px;'
                f'color:#333333;line-height:1.6;">{text}</p>'
                f'</td>'
            )
            cells = (img_cell + text_cell) if position == "left" else (text_cell + img_cell)
            html = (
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
                f'<tr>{cells}</tr></table>'
            )

        return _spacing_wrapper(html, p)


class ButtonRenderer(BlockRenderer):
    _BTN_PADDING = {
        "compact": "6px 14px",
        "normal":  "10px 24px",
        "large":   "14px 36px",
    }

    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        label          = escape(p.get("label", "Click here"))
        url            = _safe_url(p.get("url", "#"))
        bg             = escape(p.get("color", "#111827"))
        color          = escape(p.get("text_color", "#ffffff"))
        align          = escape(p.get("align", "center"))
        radius         = escape(p.get("border_radius", "8px"))
        font_size      = escape(p.get("font_size", "14px"))
        font           = font_stack(p, "Arial,sans-serif")
        btn_padding_key = p.get("button_padding", "normal")
        btn_padding    = self._BTN_PADDING.get(btn_padding_key, self._BTN_PADDING["normal"])

        padding = _padding(p, 20, 16, 20, 16)
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr><td align="{align}" style="padding:{padding};">'
            f'<a href="{url}" style="display:inline-block;padding:{btn_padding};'
            f'background-color:{bg};color:{color};font-family:{font};'
            f'font-size:{font_size};font-weight:bold;text-decoration:none;border-radius:{radius};">'
            f'{label}</a>'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class DividerRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        color     = escape(p.get("border_color", "#e0e0e0"))
        thickness = int(p.get("thickness", 1))
        style     = escape(p.get("style", "solid"))
        width     = escape(p.get("width", "100%"))
        align     = p.get("align", "center")
        text_align = "left" if align == "left" else "right" if align == "right" else "center"

        padding = _padding(p, 16, 16, 16, 16)
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr><td style="padding:{padding};" align="{text_align}">'
            f'<hr style="border:0;border-top:{thickness}px {style} {color};'
            f'width:{width};margin:0 auto;" />'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class ColumnsRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p             = block.get("props", {})
        bg            = escape(p.get("background_color", "#ffffff"))
        show_dividers = p.get("show_dividers", False)
        divider_color = escape(p.get("divider_color", "#e5e7eb"))
        col_gap       = int(p.get("col_gap", 24))
        columns       = block.get("columns", [])

        if not columns:
            return ""

        count     = len(columns)
        col_width = round(100 / count)
        half_gap  = round(col_gap / 2)
        outer_pad = _padding(p, 20, 20, 20, 20)

        cells = ""
        for idx, col in enumerate(columns):
            col_blocks = col.get("blocks", [])
            col_html = ""
            for child in col_blocks:
                renderer = RENDERER_MAP.get(child.get("type", ""))
                if renderer:
                    col_html += renderer.render(child)

            is_last      = idx == count - 1
            left_pad     = 0 if idx == 0 else half_gap
            right_pad    = 0 if is_last  else half_gap
            border_style = (
                f"border-right:1px solid {divider_color};"
                if show_dividers and not is_last else ""
            )
            cells += (
                f'<td width="{col_width}%" valign="top"'
                f' style="padding:0 {right_pad}px 0 {left_pad}px;vertical-align:top;{border_style}">'
                f'{col_html or "&nbsp;"}'
                f'</td>'
            )

        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background-color:{bg};">'
            f'<tr><td style="padding:{outer_pad};">'
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr>{cells}</tr>'
            f'</table></td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class ContainerRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p             = block.get("props", {})
        bg            = escape(p.get("background_color", "#f8fafc"))
        border_color  = escape(p.get("border_color", "#e2e8f0"))
        border_radius = escape(p.get("border_radius", "12px"))
        layout        = p.get("layout", "column")
        gap           = int(p.get("gap", 12))
        padding       = _padding(p, 16, 16, 16, 16)
        children      = block.get("children", [])

        if not children:
            return ""  # Don't render empty containers

        def render_child(child: dict) -> str:
            renderer = RENDERER_MAP.get(child.get("type", ""))
            return renderer.render(child) if renderer else ""

        if layout == "row":
            # Side-by-side columns using table cells.
            # Honour per-child width (px or %) and align props, matching the canvas.
            count    = max(len(children), 1)
            half_gap = max(gap // 2, 0)

            # Determine explicit widths; children with no explicit width share
            # the row equally. Every cell MUST get a width attribute: email
            # clients (Gmail, Outlook) size widthless <td>s by content, which
            # collapses an image column next to a text-heavy one. Browsers
            # balance them, which is why the preview looked fine but the inbox
            # did not.
            def _child_width(child: dict):
                w = child.get("props", {}).get("width", "")
                if w and w not in ("auto", "100%", "0px", ""):
                    return w
                return None

            explicit_widths = [_child_width(c) for c in children]
            default_width   = f"{round(100 / count)}%"  # equal share for implicit cells

            # Build valign map from align prop
            _valign_map = {"left": "top", "center": "middle", "right": "bottom"}

            cells = ""
            for idx, child in enumerate(children):
                left_pad  = 0 if idx == 0 else half_gap
                right_pad = 0 if idx == len(children) - 1 else half_gap
                w = explicit_widths[idx] or default_width
                width_attr = f' width="{w}"'
                valign     = _valign_map.get(child.get("props", {}).get("align", ""), "top")
                cells += (
                    f'<td{width_attr} valign="{valign}"'
                    f' style="padding:0 {right_pad}px 0 {left_pad}px;vertical-align:top;">'
                    f'{render_child(child)}'
                    f'</td>'
                )
            inner = (
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
                f'<tr>{cells}</tr></table>'
            )
        else:
            # Column (stacked) — each child is a full-width row in a single table.
            # We use table rows with a spacer row between children instead of
            # margin/div, because Outlook ignores margin on <div>.
            rendered = [(render_child(c), c) for c in children]
            rendered = [(html, c) for html, c in rendered if html]
            rows = ""
            for idx, (child_html, _) in enumerate(rendered):
                rows += f"<tr><td>{child_html}</td></tr>"
                if idx < len(rendered) - 1 and gap:
                    rows += (
                        f'<tr><td style="height:{gap}px;line-height:{gap}px;'
                        f'font-size:{gap}px;">&nbsp;</td></tr>'
                    )
            inner = (
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
                f'{rows}</table>'
            )

        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background-color:{bg};border-radius:{border_radius};">'
            f'<tr><td style="padding:{padding};border:1px solid {border_color};'
            f'border-radius:{border_radius};">'
            f'{inner}'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class FooterRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        text  = escape(p.get("text", ""))
        bg    = escape(p.get("background_color", "#f9fafb"))
        color = escape(p.get("text_color", "#6b7280"))
        font  = font_stack(p, "Arial,sans-serif")

        padding = _padding(p, 20, 16, 20, 16)
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background-color:{bg};">'
            f'<tr><td align="center" style="padding:{padding};">'
            f'<p style="margin:0;font-family:{font};font-size:12px;'
            f'color:{color};line-height:1.5;">{text}</p>'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class SpacerRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        h  = int(p.get("height", 32))
        bg = escape(p.get("background_color", "transparent"))
        bg_style = f"background-color:{bg};" if bg and bg != "transparent" else ""
        return (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="{bg_style}">'
            f'<tr><td style="height:{h}px;line-height:{h}px;font-size:{h}px;">'
            f'&nbsp;</td></tr></table>'
        )


class QuoteRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        quote        = escape(p.get("quote", ""))
        author       = escape(p.get("author", ""))
        role         = escape(p.get("role", ""))
        style        = p.get("style", "left-border")
        quote_color  = escape(p.get("quote_color", "#111827"))
        author_color = escape(p.get("author_color", "#6b7280"))
        border_color = escape(p.get("border_color", "#e5e7eb"))
        bg           = escape(p.get("background_color", "#f9fafb"))
        quote_font   = font_stack(p, "Georgia,'Times New Roman',serif")
        meta_font    = font_stack(p, "Arial,sans-serif")
        padding      = _padding(p, 24, 16, 24, 16)

        if style == "centered":
            inner = (
                f'<p style="margin:0 0 4px;font-family:Georgia,serif;font-size:40px;'
                f'line-height:1;color:{border_color};">&ldquo;</p>'
                f'<p style="margin:0 0 16px;font-family:{quote_font};'
                f'font-size:16px;font-style:italic;color:{quote_color};line-height:1.6;">'
                f'{quote}</p>'
                f'<p style="margin:0;font-family:{meta_font};font-size:14px;'
                f'font-weight:600;color:{author_color};">{author}</p>'
                f'<p style="margin:2px 0 0;font-family:{meta_font};font-size:12px;'
                f'color:{author_color};">{role}</p>'
            )
            html = (
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
                f' style="background-color:{bg};">'
                f'<tr><td align="center" style="padding:{padding};">'
                f'{inner}'
                f'</td></tr></table>'
            )
        else:
            # Left-border style
            inner = (
                f'<p style="margin:0 0 12px;font-family:{quote_font};'
                f'font-size:16px;font-style:italic;color:{quote_color};line-height:1.6;">'
                f'{quote}</p>'
                f'<p style="margin:0;font-family:{meta_font};font-size:14px;'
                f'font-weight:600;color:{author_color};">{author}</p>'
                f'<p style="margin:2px 0 0;font-family:{meta_font};font-size:12px;'
                f'color:{author_color};">{role}</p>'
            )
            pt = int(p.get("padding_top", 24))
            pr = int(p.get("padding_right", 32))
            pb = int(p.get("padding_bottom", 24))
            pl = int(p.get("padding_left", 32))
            html = (
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
                f' style="background-color:{bg};">'
                f'<tr><td style="padding:{pt}px {pr}px {pb}px {pl}px;">'
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
                f'<tr>'
                f'<td width="4" style="background-color:{border_color};border-radius:2px;">&nbsp;</td>'
                f'<td style="padding-left:16px;">{inner}</td>'
                f'</tr></table>'
                f'</td></tr></table>'
            )
        return _spacing_wrapper(html, p)


def _social_icon_img(svg_path: str, color: str, label: str, size: int = 24) -> str:
    """Build a base64 data-URI <img> for a monochrome social icon SVG path."""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"'
        f' width="{size}" height="{size}">'
        f'<path fill="{color}" d="{svg_path}"/>'
        f'</svg>'
    )
    encoded = b64encode(svg.encode()).decode()
    return (
        f'<img src="data:image/svg+xml;base64,{encoded}"'
        f' width="{size}" height="{size}" alt="{label}"'
        f' style="display:block;border:0;">'
    )

# SVG paths from Simple Icons (https://simpleicons.org) — CC0 1.0 / brand guidelines apply
_SOCIAL_ICONS: dict[str, tuple[str, str]] = {
    "x_url": (
        "X / Twitter",
        "M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231"
        "-5.401 6.231H2.746l7.73-8.835L1.254 2.25H8.08l4.253 5.622zm"
        "-1.161 17.52h1.833L7.084 4.126H5.117z",
    ),
    "linkedin_url": (
        "LinkedIn",
        "M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037"
        "-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046"
        "c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286z"
        "M5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065z"
        "m1.782 13.019H3.555V9h3.564v11.452z"
        "M22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24"
        "h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z",
    ),
    "instagram_url": (
        "Instagram",
        "M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919"
        ".058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849"
        "-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07"
        "-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92"
        "-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849"
        ".149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069z"
        "M12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052"
        ".014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948"
        ".2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24"
        "c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98"
        ".059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947"
        "-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0z"
        "m0 5.838a6.162 6.162 0 1 0 0 12.324 6.162 6.162 0 0 0 0-12.324z"
        "M12 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm6.406-11.845a1.44 1.44 0 1 0 0 2.881 1.44 1.44 0 0 0 0-2.881z",
    ),
    "facebook_url": (
        "Facebook",
        "M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12"
        "c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43"
        "c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953"
        "H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796"
        "v8.385C19.612 23.027 24 18.062 24 12.073z",
    ),
    "youtube_url": (
        "YouTube",
        "M23.495 6.205a3.007 3.007 0 0 0-2.088-2.088c-1.87-.501-9.396-.501"
        "-9.396-.501s-7.507-.01-9.396.501A3.007 3.007 0 0 0 .527 6.205"
        "a31.247 31.247 0 0 0-.522 5.805 31.247 31.247 0 0 0 .522 5.783"
        "a3.007 3.007 0 0 0 2.088 2.088c1.868.502 9.396.502 9.396.502"
        "s7.506 0 9.396-.502a3.007 3.007 0 0 0 2.088-2.088"
        "a31.247 31.247 0 0 0 .5-5.783 31.247 31.247 0 0 0-.5-5.805z"
        "M9.609 15.601V8.408l6.264 3.602z",
    ),
    "github_url": (
        "GitHub",
        "M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385"
        ".6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04"
        "-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7"
        "c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236"
        "1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605"
        "-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22"
        "-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23"
        ".96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405"
        "2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176"
        ".765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92"
        ".42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315"
        ".21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12",
    ),
    "website_url": (
        "Website",
        "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"
        "m-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1"
        "c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3"
        "c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41"
        "c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z",
    ),
}


class SocialRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p       = block.get("props", {})
        color   = p.get("color", "#374151")
        bg      = escape(p.get("background_color", "#ffffff"))
        align   = escape(p.get("align", "center"))
        padding = _padding(p, 20, 16, 20, 16)
        icon_size = int(p.get("icon_size", 32))

        links = []
        for key, (label, svg_path) in _SOCIAL_ICONS.items():
            url = p.get(key, "").strip()
            if url:
                icon = _social_icon_img(svg_path, color, label, icon_size)
                links.append(
                    f'<a href="{_safe_url(url)}" style="display:inline-block;'
                    f'margin:4px;text-decoration:none;" title="{label}">'
                    f'{icon}</a>'
                )

        if not links:
            return ""

        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background-color:{bg};">'
            f'<tr><td align="{align}" style="padding:{padding};">'
            + "".join(links) +
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class ProductCardRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p             = block.get("props", {})
        image_url     = _abs_image_src(p.get("image_url", ""))
        title         = escape(p.get("title", ""))
        description   = escape(p.get("description", ""))
        price         = escape(p.get("price", ""))
        button_label  = escape(p.get("button_label", ""))
        button_url    = _safe_url(p.get("button_url", "#"))
        bg            = escape(p.get("background_color", "#ffffff"))
        border_color  = escape(p.get("border_color", "#e5e7eb"))
        border_radius = escape(p.get("border_radius", "12px"))
        button_color  = escape(p.get("button_color", "#111827"))
        title_color   = escape(p.get("title_color", "#111827"))
        text_color    = escape(p.get("text_color", "#6b7280"))
        font          = font_stack(p, "Arial,sans-serif")

        pt = int(p.get("padding_top", 20))
        pr = int(p.get("padding_right", 32))
        pb = int(p.get("padding_bottom", 20))
        pl = int(p.get("padding_left", 32))

        img_html = ""
        if image_url:
            img_html = (
                f'<img src="{image_url}" width="100%" alt="{title}"'
                f' style="display:block;max-width:100%;height:auto;border:0;" />'
            )

        btn_html = ""
        if button_label:
            btn_html = (
                f'<a href="{button_url}" style="display:inline-block;padding:8px 18px;'
                f'background-color:{button_color};color:#ffffff;font-family:{font};'
                f'font-size:13px;font-weight:bold;text-decoration:none;border-radius:6px;">'
                f'{button_label}</a>'
            )

        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr><td style="padding:{pt}px {pr}px {pb}px {pl}px;">'
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background-color:{bg};border:1px solid {border_color};'
            f'border-radius:{border_radius};">'
            f'<tr><td>{img_html}</td></tr>'
            f'<tr><td style="padding:16px;">'
            f'<p style="margin:0 0 6px;font-family:{font};font-size:16px;'
            f'font-weight:600;color:{title_color};line-height:1.3;">{title}</p>'
            f'<p style="margin:0 0 12px;font-family:{font};font-size:14px;'
            f'color:{text_color};line-height:1.5;">{description}</p>'
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr>'
            f'<td style="font-family:{font};font-size:18px;font-weight:700;'
            f'color:{title_color};">{price}</td>'
            f'<td align="right">{btn_html}</td>'
            f'</tr></table>'
            f'</td></tr></table>'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class VideoThumbRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p             = block.get("props", {})
        thumbnail_url = _abs_image_src(p.get("thumbnail_url", ""))
        video_url     = _safe_url(p.get("video_url", "#"))
        caption       = escape(p.get("caption", ""))
        border_radius = escape(p.get("border_radius", "8px"))
        padding       = _padding(p, 16, 16, 16, 16)

        if not thumbnail_url:
            return ""

        # In email, we link the thumbnail image to the video URL.
        # A play-button overlay is achieved via a linked image approach.
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr><td style="padding:{padding};">'
            f'<a href="{video_url}" style="display:block;text-decoration:none;">'
            f'<img src="{thumbnail_url}" width="100%" alt="Watch video"'
            f' style="display:block;max-width:100%;height:auto;border:0;'
            f'border-radius:{border_radius};" />'
            f'</a>'
        )
        if caption:
            html += (
                f'<p style="margin:8px 0 0;font-family:Arial,sans-serif;font-size:13px;'
                f'color:#6b7280;text-align:center;">'
                f'<a href="{video_url}" style="color:#111827;font-weight:600;text-decoration:none;">'
                f'&#9654; {caption}</a></p>'
            )
        html += f'</td></tr></table>'
        return _spacing_wrapper(html, p)


class LinkListRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p           = block.get("props", {})
        heading     = escape(p.get("heading", ""))
        items       = p.get("items", [])
        style       = p.get("style", "bullet")
        link_color  = escape(p.get("link_color", "#2563eb"))
        text_color  = escape(p.get("text_color", "#6b7280"))
        accent_color = escape(p.get("accent_color", "#9ca3af"))
        bg          = escape(p.get("background_color", "#ffffff"))
        font        = font_stack(p, "Arial,sans-serif")
        padding     = _padding(p, 20, 16, 20, 16)

        if not items:
            return ""

        heading_html = ""
        if heading:
            heading_html = (
                f'<p style="margin:0 0 12px;font-family:{font};font-size:13px;'
                f'font-weight:600;color:#374151;text-transform:uppercase;letter-spacing:1px;">'
                f'{heading}</p>'
            )

        rows = ""
        for i, item in enumerate(items):
            title       = escape(item.get("title", ""))
            url         = _safe_url(item.get("url", "#"))
            description = escape(item.get("description", ""))

            if style == "numbered":
                marker = f"{i + 1}."
            elif style == "none":
                marker = ""
            else:
                marker = "&bull;"

            marker_cell = (
                f'<td width="16" valign="top" style="padding:0 8px 0 0;'
                f'font-family:{font};font-size:14px;color:{accent_color};'
                f'line-height:1.5;white-space:nowrap;">{marker}</td>'
            ) if marker else ""

            desc_html = (
                f'<p style="margin:2px 0 0;font-family:{font};font-size:13px;'
                f'color:{text_color};line-height:1.5;">{description}</p>'
            ) if description else ""

            rows += (
                f'<tr><td style="padding:0 0 10px;">'
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
                f'<tr>'
                f'{marker_cell}'
                f'<td valign="top">'
                f'<a href="{url}" style="font-family:{font};font-size:14px;'
                f'font-weight:500;color:{link_color};text-decoration:underline;line-height:1.5;">'
                f'{title}</a>'
                f'{desc_html}'
                f'</td>'
                f'</tr></table>'
                f'</td></tr>'
            )

        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background-color:{bg};">'
            f'<tr><td style="padding:{padding};">'
            f'{heading_html}'
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'{rows}'
            f'</table>'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class HeaderRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p             = block.get("props", {})
        logo_url      = _abs_image_src(p.get("logo_url", ""))
        logo_height   = escape(p.get("logo_height", "40px"))
        tagline       = escape(p.get("tagline", ""))
        bg            = escape(p.get("background_color", "#ffffff"))
        align         = escape(p.get("align", "center"))
        tagline_color = escape(p.get("tagline_color", "#6b7280"))
        border_bottom = p.get("border_bottom", True)
        font          = font_stack(p, "Arial,sans-serif")
        padding       = _padding(p, 20, 16, 20, 16)

        h_px = logo_height.replace("px", "")
        if logo_url:
            logo_html = (
                f'<img src="{logo_url}" height="{h_px}" alt="Logo"'
                f' style="display:block;border:0;height:{logo_height};width:auto;" />'
            )
        else:
            logo_html = (
                f'<div style="height:{logo_height};width:120px;background:#eeeeee;'
                f'font-family:Arial,sans-serif;font-size:11px;color:#999;'
                f'display:inline-block;line-height:{logo_height};text-align:center;">Logo</div>'
            )

        tagline_html = (
            f'<p style="margin:8px 0 0;font-family:{font};font-size:13px;'
            f'color:{tagline_color};line-height:1.4;">{tagline}</p>'
        ) if tagline else ""

        border_style = "border-bottom:1px solid #e5e7eb;" if border_bottom else ""

        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background-color:{bg};{border_style}">'
            f'<tr><td align="{align}" style="padding:{padding};">'
            f'{logo_html}'
            f'{tagline_html}'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class RichTextRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p            = block.get("props", {})
        html_content = _sanitize_rich_html(p.get("html_content", ""))
        if not html_content:
            return ""

        align          = escape(p.get("align", "left"))
        size           = escape(p.get("font_size", "15px"))
        weight         = escape(str(p.get("font_weight", "400")))
        color          = escape(p.get("text_color", "#374151"))
        line_height    = escape(str(p.get("line_height", "1.6")))
        letter_spacing = escape(str(p.get("letter_spacing", "")))
        font           = font_stack(p, "Arial,sans-serif")
        padding        = _padding(p, 20, 16, 20, 16)

        ls_style = f"letter-spacing:{letter_spacing};" if letter_spacing and letter_spacing != "normal" else ""
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr><td align="{align}" style="padding:{padding};'
            f'font-family:{font};font-size:{size};color:{color};'
            f'line-height:{line_height};font-weight:{weight};{ls_style}">'
            f'{html_content}'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


RENDERER_MAP: dict[str, BlockRenderer] = {
    "hero":          HeroRenderer(),
    "section_label": SectionLabelRenderer(),
    "text":          RichTextRenderer(),
    "image":         ImageRenderer(),
    "image_text":    ImageTextRenderer(),
    "button":        ButtonRenderer(),
    "columns":       ColumnsRenderer(),
    "container":     ContainerRenderer(),
    "divider":       DividerRenderer(),
    "footer":        FooterRenderer(),
    "spacer":        SpacerRenderer(),
    "quote":         QuoteRenderer(),
    "social":        SocialRenderer(),
    "product_card":  ProductCardRenderer(),
    "video_thumb":   VideoThumbRenderer(),
    "header":        HeaderRenderer(),
    "rich_text":     RichTextRenderer(),
    "link_list":     LinkListRenderer(),
}
