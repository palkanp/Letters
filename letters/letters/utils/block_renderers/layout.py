from html import escape
from typing import Any

from .base import BlockRenderer, _class_attr, _pad_class, _padding, _spacing_wrapper


def _render_child(child: dict, ctx_ref_width: int | None = None) -> str:
    """Render a nested block via the global registry.

    Imported lazily so layout renderers (which recurse into the registry that
    imports them) don't create a circular import at module load.

    ctx_ref_width carries down the child's actual rendered width in pixels
    (e.g. ~300px for a column inside a 2-up row within a 600px email) via a
    private `_ctx_ref_width` prop. Renderers that need to reason about their
    own on-screen size in absolute pixels — currently only ImageRenderer,
    for its cover-fit aspect-ratio — read it instead of assuming the full
    600px email body, which produces the wrong crop once nested narrower
    than that.
    """
    from .registry import RENDERER_MAP
    renderer = RENDERER_MAP.get(child.get("type", ""))
    if not renderer:
        return ""
    if ctx_ref_width is not None:
        child = {**child, "props": {**child.get("props", {}), "_ctx_ref_width": ctx_ref_width}}
    return renderer.render(child)


class ColumnsRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p             = block.get("props", {})
        bg            = escape(p.get("background_color", "transparent"))
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
                f'<td class="ltr-stack" width="{col_width}%" valign="{valign}"'
                f' style="padding:0 {right_pad}px 0 {left_pad}px;vertical-align:{valign};{border_style}">'
                f'{col_html or "&nbsp;"}'
                f'</td>'
            )

        bg_style = f"background-color:{bg};" if bg and bg != "transparent" else ""
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="{bg_style}">'
            f'<tr><td style="padding:{outer_pad};">'
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr>{cells}</tr>'
            f'</table></td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class ContainerRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p             = block.get("props", {})
        bg            = escape(p.get("background_color", "transparent"))
        border_color  = escape(p.get("block_border_color") or p.get("border_color", ""))
        border_radius = escape(p.get("block_border_radius") or p.get("border_radius", "0"))
        layout        = p.get("layout", "column")
        gap           = int(p.get("gap", 12))
        padding       = _padding(p, 16, 16, 16, 16)
        children      = block.get("children", [])
        # Trim wide side padding on phones so content isn't squeezed into a
        # narrow strip; the head <style> media query owns the mobile value.
        pad_class     = _class_attr(_pad_class(p))
        # This container's own actual rendered width, propagated down from
        # its parent (see _render_child). Defaults to the full email body —
        # correct for a top-level block, and for any container that isn't
        # itself nested inside a narrower row column. Children render inside
        # this container's own padding, so their available width is smaller
        # still — subtract it before passing anything further down.
        own_ref       = int(p.get("_ctx_ref_width", 600))
        own_pl        = int(p.get("padding_left",  16))
        own_pr        = int(p.get("padding_right", 16))
        content_ref   = max(own_ref - own_pl - own_pr, 1)

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
            #
            # A vertical divider is a hairline, not a content column — giving
            # it an equal 1/N share (e.g. 20% in a 3-column-plus-2-dividers
            # row) steals width from the real columns and squeezes their text
            # into a much narrower box than intended. Give dividers a small
            # fixed width instead, and share the rest among actual content.
            def _is_vdivider(child: dict) -> bool:
                return child.get("type") == "divider" and child.get("props", {}).get("orientation") == "vertical"

            def _child_width(child: dict):
                props = child.get("props", {})
                # block_width is set by image/text blocks; width is set by sub-containers
                w = props.get("block_width", "") or props.get("width", "")
                if w and w not in ("auto", "100%", "0px", ""):
                    return w
                if _is_vdivider(child):
                    return "24px"
                return None

            explicit_widths  = [_child_width(c) for c in children]
            content_count    = sum(1 for c in children if not _is_vdivider(c)) or 1
            default_width    = f"{round(100 / content_count)}%"  # equal share among real content cells

            # Map the parent container's vertical_align to HTML valign for all cells
            _va_map = {"center": "middle", "flex-start": "top", "top": "top",
                       "flex-end": "bottom", "bottom": "bottom", "middle": "middle"}
            row_valign   = _va_map.get(p.get("vertical_align", ""), "top")
            valign_css   = {"top": "top", "middle": "middle", "bottom": "bottom"}.get(row_valign, "top")

            # A price/button (or similar short label + button) pair is meant to
            # always sit on one line, even cramped, rather than break onto two
            # rows on mobile. Detect that shape automatically — via an explicit
            # mobile_stack=False, or a 2-cell row where one cell is a button —
            # so existing saved letters get the fix without needing their
            # stored block JSON re-saved from an updated preset.
            has_button   = any(c.get("type") == "button" for c in children)
            auto_no_stack = count == 2 and has_button

            # Narrow, uniform-width rows (4+ short content items, e.g. a stat
            # strip) waste most of the screen if each stacks to full width on
            # mobile — a single number+label ends up alone on a 400px-wide
            # line. Give those a 2-up grid instead; wider/fewer-column rows
            # (image+text) still need the full line once stacked, so they
            # keep ltr-stack. Dividers don't count toward "how many columns"
            # here — they're hairlines, not stat items.
            content_implicit = [
                w for c, w in zip(children, explicit_widths) if not _is_vdivider(c)
            ]
            if p.get("mobile_stack", not auto_no_stack) is False:
                stack_cls = ""
            elif content_count >= 4 and all(w is None for w in content_implicit):
                stack_cls = "ltr-stack-2"
            else:
                stack_cls = "ltr-stack"

            def _cell_ref_width(w: str) -> int:
                # Resolve this cell's own width (percent or px) against the
                # row's actual available content width (this container's own
                # width minus its own padding) — not a fixed 600px
                # assumption — otherwise a narrow column's images compute
                # their cover-fit aspect-ratio against too much width and
                # end up over-cropped/zoomed.
                if w.endswith("px"):
                    try:
                        return max(int(w[:-2]), 1)
                    except ValueError:
                        return content_ref
                if w.endswith("%"):
                    try:
                        return max(round(content_ref * int(w[:-1]) / 100), 1)
                    except ValueError:
                        return content_ref
                return content_ref

            cells = ""
            for idx, child in enumerate(children):
                left_pad  = 0 if idx == 0 else half_gap
                right_pad = 0 if idx == len(children) - 1 else half_gap
                w = explicit_widths[idx] or default_width
                width_attr = f' width="{w}"'
                # The cell's own gap padding also eats into the child's real
                # rendered width.
                cell_ref = max(_cell_ref_width(w) - left_pad - right_pad, 1)
                # A vertical divider between stacked columns should read as a
                # horizontal rule once those columns stack full-width on
                # mobile, not a 1px-wide sliver floating in the middle of a
                # full-width row.
                cell_cls = "ltr-vdivider" if (stack_cls and _is_vdivider(child)) else stack_cls
                cells += (
                    f'<td{_class_attr(cell_cls)}{width_attr} valign="{row_valign}"'
                    f' style="padding:0 {right_pad}px 0 {left_pad}px;vertical-align:{valign_css};">'
                    f'{_render_child(child, cell_ref)}'
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
            rendered = [(_render_child(c, content_ref), c) for c in children]
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

        border_style = f"border:1px solid {border_color};" if border_color else ""
        radius_style = f"border-radius:{border_radius};" if border_radius and border_radius != "0" else ""
        bg_style     = f"background-color:{bg};" if bg and bg != "transparent" else ""
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="{bg_style}{radius_style}">'
            f'<tr><td{pad_class} style="padding:{padding};{border_style}{radius_style}">'
            f'{inner}'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class DividerRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        color       = escape(p.get("border_color", "#e0e0e0"))
        thickness   = int(p.get("thickness", 1))
        style       = escape(p.get("style", "solid"))
        orientation = p.get("orientation", "horizontal")
        padding     = _padding(p, 16, 16, 16, 16)

        if orientation == "vertical":
            height = int(p.get("height", 80))
            border_style = (
                f"border-left:{thickness}px {style} {color};"
                if style != "solid"
                else f"background-color:{color};"
            )
            html = (
                f'<table cellpadding="0" cellspacing="0" border="0">'
                f'<tr><td style="padding:{padding};text-align:center;">'
                f'<div style="display:inline-block;width:{thickness}px;height:{height}px;{border_style}"></div>'
                f'</td></tr></table>'
            )
        else:
            width      = escape(p.get("width", "100%"))
            align      = p.get("align", "center")
            text_align = "left" if align == "left" else "right" if align == "right" else "center"
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
