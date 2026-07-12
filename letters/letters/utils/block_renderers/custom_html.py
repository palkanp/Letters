from typing import Any

from .base import BlockRenderer, _padding, _spacing_wrapper


class CustomHtmlRenderer(BlockRenderer):
    """Passes the author's HTML straight through, unescaped and unsanitized.

    Unlike every other renderer, this is a deliberate escape hatch: it exists
    so advanced letters (JSON-LD event markup, hand-built table layouts ported
    from a legacy campaign, etc.) aren't blocked by the visual builder's fixed
    set of blocks. Access to this block type should be limited to trusted
    roles at the UI layer — there is no sanitization to fall back on here.
    """

    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {}) or {}
        html = p.get("html", "") or ""
        if not html.strip():
            return ""
        padding = _padding(p, 0, 0, 0, 0)
        # The email-card <td> zeroes font-size/line-height (the inline-gap
        # killer in the outer wrapper); every other renderer resets them inside
        # its own markup, but raw author HTML inherits them — any multi-line
        # content without an explicit line-height collapses onto a single
        # overlapping line. Reset here; author inline styles still win.
        wrapped = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr><td style="padding:{padding};font-size:14px;line-height:1.6;">{html}</td></tr></table>'
        )
        return _spacing_wrapper(wrapped, p)
