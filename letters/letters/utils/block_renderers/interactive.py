from html import escape
from typing import Any

from letters.letters.utils.fonts import font_stack
from .base import BlockRenderer, _padding, _safe_url, _spacing_wrapper


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
        letter_spacing = escape(p.get("letter_spacing", ""))
        ls_style       = f"letter-spacing:{letter_spacing};" if letter_spacing and letter_spacing != "normal" else ""
        outer_bg       = escape(p.get("background_color", ""))
        outer_bg_style = f"background-color:{outer_bg};" if outer_bg and outer_bg not in ("transparent", "") else ""

        padding = _padding(p, 20, 16, 20, 16)
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="{outer_bg_style}">'
            f'<tr><td align="{align}" style="padding:{padding};">'
            f'<a href="{url}" style="display:inline-block;padding:{btn_padding};'
            f'background-color:{bg};color:{color};font-family:{font};'
            f'font-size:{font_size};font-weight:500;text-decoration:none;'
            f'border-radius:{radius};{ls_style}">'
            f'{label}</a>'
            f'</td></tr></table>'
        )
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
                f'<p style="margin:5px 0 0;font-family:{font};font-size:13px;'
                f'color:{text_color};line-height:1.6;">{description}</p>'
            ) if description else ""

            rows += (
                f'<tr><td style="padding:0 0 12px;">'
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
