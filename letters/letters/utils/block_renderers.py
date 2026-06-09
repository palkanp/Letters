from abc import ABC, abstractmethod
from html import escape
from typing import Any


def _padding(props: dict, dt: int = 20, dr: int = 32, db: int = 20, dl: int = 32) -> str:
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
        padding         = _padding(p, 40, 32, 40, 32)

        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background-color:{bg};">'
            f'<tr><td align="{text_align}" style="padding:{padding};">'
            f'<h1 style="margin:0 0 12px;font-family:Georgia,\'Times New Roman\',serif;'
            f'font-size:{heading_size};font-weight:bold;color:{heading_color};'
            f'line-height:1.2;text-align:{text_align};">{heading}</h1>'
            f'<p style="margin:0;font-family:Arial,sans-serif;font-size:16px;'
            f'color:{subheading_color};line-height:1.5;text-align:{text_align};">{subheading}</p>'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class TextRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        content        = escape(p.get("content", ""))
        align          = escape(p.get("align", "left"))
        size           = escape(p.get("font_size", "15px"))
        weight         = escape(str(p.get("font_weight", "400")))
        color          = escape(p.get("text_color", "#333333"))
        line_height    = escape(str(p.get("line_height", "1.6")))
        letter_spacing = escape(p.get("letter_spacing", "normal"))

        padding = _padding(p, 20, 32, 20, 32)
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr><td align="{align}" style="padding:{padding};">'
            f'<p style="margin:0;font-family:Arial,sans-serif;font-size:{size};'
            f'color:{color};line-height:{line_height};text-align:{align};'
            f'font-weight:{weight};letter-spacing:{letter_spacing};">{content}</p>'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class ImageRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        image_url     = escape(p.get("image_url", ""))
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

        caption_html = ""
        if caption:
            caption_html = (
                f'<tr><td style="padding:6px 32px 0;font-family:Arial,sans-serif;'
                f'font-size:12px;color:{caption_color};line-height:1.4;">{caption}</td></tr>'
            )

        padding = _padding(p, 16, 32, 16, 32)
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background-color:{bg};">'
            f'<tr><td style="padding:{padding};">'
            f'<img src="{image_url}" width="100%" alt="{alt}"'
            f' style="display:block;max-width:100%;height:auto;{border_style}{radius_style}" />'
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

        line_html = f'<hr style="border:0;border-top:1px solid {line_color};margin:8px 0 0;" />'
        above_line = line_html if line_position == "above" else ""
        below_line = line_html if line_position in ("below", "") or not line_position else ""

        padding = _padding(p, 12, 32, 12, 32)
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr><td style="padding:{padding};" align="{align}">'
            f'{above_line}'
            f'<span style="font-family:Arial,sans-serif;font-size:{font_size};font-weight:{font_weight};'
            f'color:{text_color};text-transform:uppercase;letter-spacing:0.99px;'
            f'line-height:1.2;">{label}</span>'
            f'{below_line}'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class ImageTextRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        image_url   = escape(p.get("image_url", ""))
        text        = escape(p.get("text", ""))
        position    = p.get("image_position", "left")
        img_width   = p.get("image_width", "160px")
        layout_mode = p.get("layout_mode", "side")

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
                f'<p style="margin:0;font-family:Arial,sans-serif;font-size:15px;'
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
                f'<p style="margin:0;font-family:Arial,sans-serif;font-size:15px;'
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
        url            = escape(p.get("url", "#"))
        bg             = escape(p.get("color", "#111827"))
        color          = escape(p.get("text_color", "#ffffff"))
        align          = escape(p.get("align", "center"))
        radius         = escape(p.get("border_radius", "8px"))
        font_size      = escape(p.get("font_size", "14px"))
        btn_padding_key = p.get("button_padding", "normal")
        btn_padding    = self._BTN_PADDING.get(btn_padding_key, self._BTN_PADDING["normal"])

        padding = _padding(p, 20, 32, 20, 32)
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr><td align="{align}" style="padding:{padding};">'
            f'<a href="{url}" style="display:inline-block;padding:{btn_padding};'
            f'background-color:{bg};color:{color};font-family:Arial,sans-serif;'
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

        padding = _padding(p, 16, 32, 16, 32)
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
        p = block.get("props", {})
        bg             = escape(p.get("background_color", "#ffffff"))
        heading_color  = escape(p.get("heading_color", "#111827"))
        text_color     = escape(p.get("text_color", "#6b7280"))
        button_color   = escape(p.get("button_color", "#111827"))
        show_dividers  = p.get("show_dividers", False)
        divider_color  = escape(p.get("divider_color", "#e5e7eb"))
        col_gap        = int(p.get("col_gap", 24))
        cols           = p.get("columns", [])
        count          = max(len(cols), 1)
        col_width      = round(100 / count)
        half_gap       = round(col_gap / 2)

        outer_pad = _padding(p, 20, 20, 20, 20)
        cells = ""
        for idx, col in enumerate(cols):
            heading   = escape(col.get("heading", ""))
            text      = escape(col.get("text", ""))
            btn_label = escape(col.get("button_label", ""))
            btn_url   = escape(col.get("button_url", "#"))
            is_last   = idx == len(cols) - 1

            heading_html = ""
            if heading:
                heading_html = (
                    f'<p style="margin:0 0 6px;font-family:Arial,sans-serif;font-size:16px;'
                    f'font-weight:600;color:{heading_color};line-height:1.3;">{heading}</p>'
                )

            btn_html = ""
            if btn_label:
                btn_html = (
                    f'<p style="margin:12px 0 0;">'
                    f'<a href="{btn_url}" style="display:inline-block;padding:8px 20px;'
                    f'background-color:{button_color};color:#ffffff;font-family:Arial,sans-serif;'
                    f'font-size:13px;font-weight:bold;text-decoration:none;border-radius:4px;">'
                    f'{btn_label}</a></p>'
                )

            left_pad  = 0 if idx == 0 else half_gap
            right_pad = 0 if is_last  else half_gap
            border_style = (
                f'border-right:1px solid {divider_color};' if show_dividers and not is_last else ""
            )

            cells += (
                f'<td width="{col_width}%" valign="top"'
                f' style="padding:0 {right_pad}px 0 {left_pad}px;vertical-align:top;{border_style}">'
                f'{heading_html}'
                f'<p style="margin:0;font-family:Arial,sans-serif;font-size:14px;'
                f'color:{text_color};line-height:1.6;">{text}</p>'
                f'{btn_html}'
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
        p = block.get("props", {})
        heading       = escape(p.get("heading", ""))
        text          = escape(p.get("text", ""))
        bg            = escape(p.get("background_color", "#f8fafc"))
        border_color  = escape(p.get("border_color", "#e2e8f0"))
        border_radius = escape(p.get("border_radius", "12px"))
        padding       = _padding(p, 24, 24, 24, 24)

        heading_html = ""
        if heading:
            heading_html = (
                f'<p style="margin:0 0 8px;font-family:Arial,sans-serif;font-size:16px;'
                f'font-weight:600;color:#111827;line-height:1.3;">{heading}</p>'
            )
        text_html = ""
        if text:
            text_html = (
                f'<p style="margin:0;font-family:Arial,sans-serif;font-size:14px;'
                f'color:#6b7280;line-height:1.6;">{text}</p>'
            )

        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background-color:{bg};border-radius:{border_radius};">'
            f'<tr><td style="padding:{padding};border:1px solid {border_color};'
            f'border-radius:{border_radius};">'
            f'{heading_html}{text_html}'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class FooterRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        text  = escape(p.get("text", ""))
        bg    = escape(p.get("background_color", "#f9fafb"))
        color = escape(p.get("text_color", "#6b7280"))

        padding = _padding(p, 20, 32, 20, 32)
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background-color:{bg};">'
            f'<tr><td align="center" style="padding:{padding};">'
            f'<p style="margin:0;font-family:Arial,sans-serif;font-size:12px;'
            f'color:{color};line-height:1.5;">{text}</p>'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


RENDERER_MAP: dict[str, BlockRenderer] = {
    "hero":          HeroRenderer(),
    "section_label": SectionLabelRenderer(),
    "text":          TextRenderer(),
    "image":         ImageRenderer(),
    "image_text":    ImageTextRenderer(),
    "button":        ButtonRenderer(),
    "columns":       ColumnsRenderer(),
    "container":     ContainerRenderer(),
    "divider":       DividerRenderer(),
    "footer":        FooterRenderer(),
}
