from html import escape
from typing import Any

from .base import BlockRenderer, _padding, _spacing_wrapper


def _render_child(child: dict) -> str:
    """Render a nested block via the global registry.

    Imported lazily so layout renderers (which recurse into the registry that
    imports them) don't create a circular import at module load.
    """
    from .registry import RENDERER_MAP
    renderer = RENDERER_MAP.get(child.get("type", ""))
    return renderer.render(child) if renderer else ""


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

        _valign_map = {
            "top": "top", "middle": "middle", "bottom": "bottom",
            "flex-start": "top", "center": "middle", "flex-end": "bottom",
        }
        valign = _valign_map.get(p.get("vertical_align", "top"), "top")

        cells = ""
        for idx, col in enumerate(columns):
            col_blocks = col.get("blocks", [])
            col_html = ""
            for child in col_blocks:
                col_html += _render_child(child)

            is_last      = idx == count - 1
            left_pad     = 0 if idx == 0 else half_gap
            right_pad    = 0 if is_last  else half_gap
            border_style = (
                f"border-right:1px solid {divider_color};"
                if show_dividers and not is_last else ""
            )
            cells += (
                f'<td width="{col_width}%" valign="{valign}"'
                f' style="padding:0 {right_pad}px 0 {left_pad}px;vertical-align:{valign};{border_style}">'
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
                    f'{_render_child(child)}'
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
            rendered = [(_render_child(c), c) for c in children]
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
