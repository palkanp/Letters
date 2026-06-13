from html import escape
from html.parser import HTMLParser
from typing import Any, List, Optional, Tuple

from letters.letters.utils.fonts import font_stack
from .base import BlockRenderer, _padding, _safe_url, _spacing_wrapper


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
                    f'<a href="{safe}" target="_blank">'
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
        # Normalise <p> tags: reset email-client default margins and apply text-align.
        # Email clients (Gmail, Outlook) add ~1em top+bottom margin to <p> by default,
        # which creates unintended gaps. We own the outer block padding so p gets 0 margin.
        # The last <p> gets margin:0 so it doesn't bleed past the block's padding_bottom.
        p_style = "margin:0 0 0.75em 0;"
        p_last_style = "margin:0;"
        if align and align != "left":
            p_style += f"text-align:{align};"
            p_last_style += f"text-align:{align};"
        html_content = html_content.replace("<p>", f"<p style=\"{p_style}\">")
        # Lists: use inside positioning so markers stay next to text even when the
        # block is center-aligned. Email clients default to outside + browser padding,
        # which pushes numbers/bullets far from the text on non-left-aligned blocks.
        list_style = "list-style-position:inside;padding-left:0;margin:0.5em 0;"
        html_content = html_content.replace("<ul>", f'<ul style="{list_style}">')
        html_content = html_content.replace("<ol>", f'<ol style="{list_style}">')
        # Replace only the final </p> to apply the last-paragraph zero margin.
        last_close = html_content.rfind("</p>")
        if last_close != -1:
            # Find the matching opening tag just before last_close and swap its style
            last_open = html_content.rfind("<p ", 0, last_close)
            if last_open != -1:
                tag_end = html_content.index(">", last_open)
                html_content = (
                    html_content[:last_open]
                    + f'<p style="{p_last_style}">'
                    + html_content[tag_end + 1:]
                )
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr><td align="{align}" style="padding:{padding};'
            f'font-family:{font};font-size:{size};color:{color};'
            f'line-height:{line_height};font-weight:{weight};{ls_style}">'
            f'{html_content}'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)
