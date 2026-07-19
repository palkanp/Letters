from html import escape
from typing import Any

from letters.letters.utils.fonts import font_stack
from .base import BlockRenderer, _abs_image_src, _class_attr, _font_scale_class, _pad_class, _padding, _safe_css_value, _safe_url, _spacing_wrapper


class HeroRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        bg              = _safe_css_value(p.get("background_color", "#ffffff"))
        heading         = escape(p.get("heading", ""))
        subheading      = escape(p.get("subheading", ""))
        heading_color   = _safe_css_value(p.get("heading_color", "#111827"))
        heading_size    = _safe_css_value(p.get("heading_size", "30px"))
        subheading_color = _safe_css_value(p.get("subheading_color", "#6b7280"))
        text_align      = _safe_css_value(p.get("text_align", "center"))
        heading_font    = font_stack(p, "Georgia,'Times New Roman',serif")
        subheading_font = font_stack(p, "Arial,sans-serif")
        padding         = _padding(p, 40, 16, 40, 16)

        fs_class = _font_scale_class(heading_size)
        h1_class = f' class="{fs_class}"' if fs_class else ""
        heading_html = (
            f'<h1{h1_class} style="margin:0 0 12px;font-family:{heading_font};'
            f'font-size:{heading_size};font-weight:bold;color:{heading_color};'
            f'line-height:1.2;text-align:{text_align};">{heading}</h1>'
        ) if heading else ""
        subheading_html = (
            f'<p style="margin:0;font-family:{subheading_font};font-size:16px;'
            f'color:{subheading_color};line-height:1.5;text-align:{text_align};">{subheading}</p>'
        ) if subheading else ""

        pad_class = _class_attr(_pad_class(p, 40, 16))
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background-color:{bg};">'
            f'<tr><td align="{text_align}"{pad_class} style="padding:{padding};">'
            f'{heading_html}{subheading_html}'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class SectionLabelRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        label          = escape(p.get("label", ""))
        text_color     = _safe_css_value(p.get("text_color", "#383838"))
        line_color     = _safe_css_value(p.get("line_color", "#ededed"))
        line_thickness = p.get("line_thickness", 0.5)
        line_position  = p.get("line_position", "below")
        align          = _safe_css_value(p.get("align", "left"))
        font_size      = _safe_css_value(p.get("font_size", "11px"))
        font_weight    = _safe_css_value(str(p.get("font_weight", "600")))
        letter_spacing = _safe_css_value(p.get("letter_spacing", "0.15em"))
        font           = font_stack(p, "Arial,sans-serif")

        line_html = f'<hr style="border:0;border-top:{line_thickness}px solid {line_color};margin:8px 0 0;" />'
        above_line = line_html if line_position == "above" else ""
        below_line = line_html if line_position in ("below", "") or not line_position else ""

        padding = _padding(p, 12, 16, 12, 16)
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f'<tr><td{_class_attr(_pad_class(p))} style="padding:{padding};" align="{align}">'
            f'{above_line}'
            f'<span style="font-family:{font};font-size:{font_size};font-weight:{font_weight};'
            f'color:{text_color};text-transform:uppercase;letter-spacing:{letter_spacing};'
            f'line-height:1.2;">{label}</span>'
            f'{below_line}'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class FooterRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        text  = escape(p.get("text", ""))
        bg    = _safe_css_value(p.get("background_color", "#f9fafb"))
        color = _safe_css_value(p.get("text_color", "#6b7280"))
        font  = font_stack(p, "Arial,sans-serif")

        padding = _padding(p, 20, 16, 20, 16)

        text_html = (
            f'<p style="margin:0;font-family:{font};font-size:12px;'
            f'color:{color};line-height:1.5;">{text}</p>'
        ) if text else ""

        # Compliance / service links (unsubscribe, preferences…) rendered as a
        # single centered line. URLs may be merge-tag expressions resolved at
        # send time — _safe_url passes those through untouched.
        link_color = _safe_css_value(p.get("link_color", "")) or color
        parts = []
        for link in p.get("links") or []:
            label = escape((link or {}).get("label", "").strip())
            if not label:
                continue
            url = _safe_url((link or {}).get("url", "#"))
            parts.append(
                f'<a href="{url}" style="color:{link_color};'
                f'text-decoration:underline;">{label}</a>'
            )
        links_html = ""
        if parts:
            sep = f'<span style="color:{color};">&nbsp;&nbsp;&middot;&nbsp;&nbsp;</span>'
            margin_top = "8px" if text_html else "0"
            links_html = (
                f'<p style="margin:{margin_top} 0 0;font-family:{font};font-size:12px;'
                f'color:{color};line-height:1.5;">{sep.join(parts)}</p>'
            )

        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background-color:{bg};">'
            f'<tr><td align="center"{_class_attr(_pad_class(p))} style="padding:{padding};">'
            f'{text_html}{links_html}'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class HeaderRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p             = block.get("props", {})
        logo_url      = _abs_image_src(p.get("logo_url", ""))
        logo_height   = _safe_css_value(p.get("logo_height", "40px"))
        tagline       = escape(p.get("tagline", ""))
        bg            = _safe_css_value(p.get("background_color", "#ffffff"))
        align         = _safe_css_value(p.get("align", "center"))
        tagline_color = _safe_css_value(p.get("tagline_color", "#6b7280"))
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
        pad_class = _class_attr(_pad_class(p))

        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background-color:{bg};{border_style}">'
            f'<tr><td align="{align}"{pad_class} style="padding:{padding};">'
            f'{logo_html}'
            f'{tagline_html}'
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)


class QuoteRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        quote        = escape(p.get("quote", ""))
        author       = escape(p.get("author", ""))
        role         = escape(p.get("role", ""))
        style        = p.get("style", "left-border")
        quote_color  = _safe_css_value(p.get("quote_color", "#111827"))
        author_color = _safe_css_value(p.get("author_color", "#6b7280"))
        border_color = _safe_css_value(p.get("border_color", "#e5e7eb"))
        bg           = _safe_css_value(p.get("background_color", "#f9fafb"))
        quote_font   = font_stack(p, "Georgia,'Times New Roman',serif")
        meta_font    = font_stack(p, "Arial,sans-serif")
        padding      = _padding(p, 24, 16, 24, 16)

        if style == "centered":
            inner = (
                f'<p class="ltr-fs-xl" style="margin:0 0 4px;font-family:Georgia,serif;font-size:40px;'
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
                f'<tr><td align="center"{_class_attr(_pad_class(p, 24, 16))} style="padding:{padding};">'
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
                f'<tr><td{_class_attr(_pad_class(p, 32, 32))} style="padding:{pt}px {pr}px {pb}px {pl}px;">'
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
                f'<tr>'
                f'<td width="4" style="background-color:{border_color};border-radius:2px;">&nbsp;</td>'
                f'<td style="padding-left:16px;">{inner}</td>'
                f'</tr></table>'
                f'</td></tr></table>'
            )
        return _spacing_wrapper(html, p)
