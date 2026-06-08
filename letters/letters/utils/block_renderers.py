from abc import ABC, abstractmethod
from html import escape
from typing import Any


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

        padding_map = {"compact": "24px 32px", "normal": "40px 32px", "spacious": "64px 32px"}
        padding = padding_map.get(p.get("padding", "normal"), "40px 32px")

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

        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr><td align="{align}" style="padding:12px 32px;">'
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

        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background-color:{bg};">'
            f'<tr><td style="padding:0 32px;">'
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

        line_html = f'<hr style="border:0;border-top:1px solid {line_color};margin:8px 0 0;" />'
        above_line = line_html if line_position == "above" else ""
        below_line = line_html if line_position in ("below", "") or not line_position else ""

        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr><td style="padding:16px 32px 8px;" align="{align}">'
            f'{above_line}'
            f'<span style="font-family:Arial,sans-serif;font-size:11px;font-weight:600;'
            f'color:{text_color};text-transform:uppercase;letter-spacing:0.99px;'
            f'line-height:1.2;">{label}</span>'
            f'{below_line}'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class ImageTextRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        image_url = escape(p.get("image_url", ""))
        text      = escape(p.get("text", ""))
        position  = p.get("image_position", "left")
        img_width = p.get("image_width", "175px")

        # Convert percentage widths to approximate pixel widths for email
        width_map = {"25%": "140", "33%": "180", "50%": "260", "175px": "175"}
        img_px = width_map.get(img_width, "175")

        img_cell = (
            f'<td width="{img_px}" valign="top" style="padding:16px 8px 16px 32px;">'
            f'<img src="{image_url}" width="{img_px}" style="display:block;border:0;" alt="" />'
            f'</td>'
        ) if image_url else (
            f'<td width="{img_px}" valign="top" style="padding:16px 8px 16px 32px;">'
            f'<div style="width:{img_px}px;height:100px;background:#eeeeee;'
            f'font-family:Arial,sans-serif;font-size:12px;color:#999;text-align:center;'
            f'padding-top:40px;">Image</div>'
            f'</td>'
        )
        text_cell = (
            f'<td valign="top" style="padding:16px 32px 16px 8px;">'
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
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        label  = escape(p.get("label", "Click here"))
        url    = escape(p.get("url", "#"))
        bg     = escape(p.get("color", "#6366f1"))
        color  = escape(p.get("text_color", "#ffffff"))
        align  = escape(p.get("align", "center"))
        radius = escape(p.get("border_radius", "8px"))

        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr><td align="{align}" style="padding:16px 32px;">'
            f'<a href="{url}" style="display:inline-block;padding:12px 28px;'
            f'background-color:{bg};color:{color};font-family:Arial,sans-serif;'
            f'font-size:15px;font-weight:bold;text-decoration:none;border-radius:{radius};">'
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

        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr><td style="padding:8px 32px;">'
            f'<hr style="border:0;border-top:{thickness}px {style} {color};margin:0;" />'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class ColumnsRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        bg            = escape(p.get("background_color", "#ffffff"))
        heading_color = escape(p.get("heading_color", "#111827"))
        text_color    = escape(p.get("text_color", "#6b7280"))
        button_color  = escape(p.get("button_color", "#111827"))
        cols          = p.get("columns", [])
        count         = max(len(cols), 1)
        col_width     = round(100 / count)

        cells = ""
        for col in cols:
            heading   = escape(col.get("heading", ""))
            text      = escape(col.get("text", ""))
            btn_label = escape(col.get("button_label", ""))
            btn_url   = escape(col.get("button_url", "#"))
            btn_html  = ""
            if btn_label:
                btn_html = (
                    f'<p style="margin:12px 0 0;">'
                    f'<a href="{btn_url}" style="display:inline-block;padding:8px 20px;'
                    f'background-color:{button_color};color:#ffffff;font-family:Arial,sans-serif;'
                    f'font-size:13px;font-weight:bold;text-decoration:none;border-radius:4px;">'
                    f'{btn_label}</a></p>'
                )
            cells += (
                f'<td width="{col_width}%" valign="top"'
                f' style="padding:16px 12px;vertical-align:top;">'
                f'<h3 style="margin:0 0 8px;font-family:Georgia,serif;font-size:16px;'
                f'font-weight:600;color:{heading_color};line-height:1.3;">{heading}</h3>'
                f'<p style="margin:0;font-family:Arial,sans-serif;font-size:14px;'
                f'color:{text_color};line-height:1.6;">{text}</p>'
                f'{btn_html}'
                f'</td>'
            )

        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background-color:{bg};">'
            f'<tr>{cells}</tr></table>'
        )
        return _spacing_wrapper(html, p)


class FooterRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        text  = escape(p.get("text", ""))
        bg    = escape(p.get("background_color", "#f9fafb"))
        color = escape(p.get("text_color", "#6b7280"))

        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background-color:{bg};">'
            f'<tr><td align="center" style="padding:24px 32px;">'
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
    "divider":       DividerRenderer(),
    "footer":        FooterRenderer(),
}
