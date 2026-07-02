from html import escape
from typing import Any

from letters.letters.utils.fonts import font_stack
from .base import (
    BlockRenderer,
    _abs_image_src,
    _aspect_ref_width,
    _class_attr,
    _pad_class,
    _padding,
    _safe_url,
    _spacing_wrapper,
)


class ImageRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        image_url     = _abs_image_src(p.get("image_url", ""))
        alt           = escape(p.get("alt", ""))
        bg            = escape(p.get("background_color", "#ffffff"))
        border        = escape(p.get("border", ""))
        border_radius = escape(p.get("border_radius", "0"))
        image_width   = p.get("image_width", "100%") or "100%"
        image_height  = p.get("image_height", "") or ""
        image_align   = p.get("image_align", "center") or "center"
        image_fit     = p.get("image_fit", "cover") or "cover"

        border_style = f"border:{border};" if border and border != "none" else ""
        radius_style = f"border-radius:{border_radius};" if border_radius and border_radius != "0" else ""

        if not image_url:
            return ""  # Don't render empty image blocks

        link_url = _safe_url(p.get("link_url", ""))

        # Build width / height attributes for email-safe rendering.
        # Pixel widths use a width attribute; percent widths use max-width in CSS.
        if image_width.endswith("px"):
            w_attr  = f' width="{image_width.replace("px", "")}"'
            w_style = f"width:{image_width};max-width:100%;"
        elif image_width == "100%":
            w_attr  = ' width="100%"'
            w_style = "width:100%;max-width:100%;"
        else:
            w_attr  = ""
            w_style = f"width:{image_width};max-width:100%;"

        if image_height and image_height != "auto":
            h_num   = image_height.replace("px", "")
            h_attr  = f' height="{h_num}"'
            obj_pos = escape(p.get("object_position", "center") or "center")
            if image_fit == "cover":
                # Preserve the crop proportionally on small screens: give the box
                # a fixed aspect-ratio instead of a frozen pixel height, so width
                # and height shrink together (keeps object-position focus, avoids
                # the zoomed-in crop a frozen height produces when only the width
                # scales down). The height attr stays for Outlook's Word engine,
                # which ignores aspect-ratio.
                ref_w   = _aspect_ref_width(image_width)
                h_style = (
                    f"height:auto;aspect-ratio:{ref_w}/{h_num};"
                    f"object-fit:cover;object-position:{obj_pos};"
                )
            else:
                h_style = f"height:{image_height};object-fit:{image_fit};object-position:{obj_pos};"
        else:
            h_attr  = ""
            h_style = "height:auto;"

        align_map = {"left": "left", "center": "center", "right": "right"}
        td_align  = align_map.get(image_align, "center")

        img_tag = (
            f'<img src="{image_url}"{w_attr}{h_attr} alt="{alt}"'
            f' style="display:block;{w_style}{h_style}{border_style}{radius_style}" />'
        )
        img_content = (
            f'<a href="{link_url}" style="display:block;text-decoration:none;">{img_tag}</a>'
            if link_url and link_url != "#"
            else img_tag
        )

        caption = escape(p.get("caption", ""))
        padding = _padding(p, 16, 16, 16, 16)
        pad_class = _class_attr(_pad_class(p))
        caption_row = (
            f'<tr><td align="{td_align}" style="padding:4px 0 0;font-family:Arial,sans-serif;'
            f'font-size:12px;color:#6b7280;">{caption}</td></tr>'
        ) if caption else ""
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background-color:{bg};">'
            f'<tr><td align="{td_align}"{pad_class} style="padding:{padding};">'
            f'{img_content}'
            f'</td></tr>'
            f'{caption_row}'
            f'</table>'
        )
        return _spacing_wrapper(html, p)


class ImageTextRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p = block.get("props", {})
        image_url     = _abs_image_src(p.get("image_url", ""))
        text          = escape(p.get("text", ""))
        heading_text  = escape(p.get("heading", ""))
        heading_color = escape(p.get("heading_color", "#111827"))
        position      = p.get("image_position", "left")
        img_width     = p.get("image_width", "160px")
        layout_mode   = p.get("layout_mode", "side")
        font          = font_stack(p, "Arial,sans-serif")

        img_px = img_width.replace("px", "") if img_width.endswith("px") else "160"
        bg     = escape(p.get("background_color", ""))
        bg_style = f"background-color:{bg};" if bg and bg not in ("transparent", "") else ""

        pt = int(p.get("padding_top",    20))
        pr = int(p.get("padding_right",  16))
        pb = int(p.get("padding_bottom", 20))
        pl = int(p.get("padding_left",   16))
        pad_class = _class_attr(_pad_class(p))

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
            heading_html = (
                f'<p style="margin:0 0 6px;font-family:{font};font-size:16px;'
                f'font-weight:700;color:{heading_color};line-height:1.3;">{heading_text}</p>'
            ) if heading_text else ""
            text_color = escape(p.get("text_color", "#555555"))
            html = (
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
                f' style="{bg_style}">'
                f'<tr><td{pad_class} style="padding:{pt}px {pr}px {pb}px {pl}px;">'
                f'{img_html}'
                f'{heading_html}'
                f'<p style="margin:0;font-family:{font};font-size:15px;'
                f'color:{text_color};line-height:1.6;">{text}</p>'
                f'</td></tr></table>'
            )
        else:
            # Side-by-side (default)
            # Block padding wraps the outer table; inner cells only need the gap between image and text.
            gap          = 20
            outer_pad    = f"{pt}px {pr}px {pb}px {pl}px"
            text_color   = escape(p.get("text_color", "#555555"))
            img_pad      = f"0 {gap}px 0 0" if position == "left" else f"0 0 0 {gap}px"
            text_pad_str = "0" if position == "left" else "0"
            img_cell = (
                f'<td class="ltr-stack" width="{img_px}" valign="middle" style="padding:{img_pad};">'
                f'<img src="{image_url}" width="{img_px}" style="display:block;border:0;'
                f'border-radius:4px;" alt="" />'
                f'</td>'
            ) if image_url else (
                f'<td class="ltr-stack" width="{img_px}" valign="middle" style="padding:{img_pad};">'
                f'<div style="width:{img_px}px;height:100px;background:#eeeeee;'
                f'font-family:Arial,sans-serif;font-size:12px;color:#999;text-align:center;'
                f'padding-top:40px;">Image</div>'
                f'</td>'
            )
            heading_html = (
                f'<p style="margin:0 0 6px;font-family:{font};font-size:16px;'
                f'font-weight:700;color:{heading_color};line-height:1.3;">{heading_text}</p>'
            ) if heading_text else ""
            text_cell = (
                f'<td class="ltr-stack" valign="middle" style="padding:{text_pad_str};">'
                f'{heading_html}'
                f'<p style="margin:0;font-family:{font};font-size:15px;'
                f'color:{text_color};line-height:1.6;">{text}</p>'
                f'</td>'
            )
            cells = (img_cell + text_cell) if position == "left" else (text_cell + img_cell)
            html = (
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
                f' style="{bg_style}">'
                f'<tr><td{pad_class} style="padding:{outer_pad};">'
                f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
                f'<tr>{cells}</tr>'
                f'</table>'
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
        pad_class = _class_attr(_pad_class(p, 32, 32))

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
            f'<tr><td{pad_class} style="padding:{pt}px {pr}px {pb}px {pl}px;">'
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
            f'<td style="font-family:{font};font-size:18px;font-weight:400;'
            f'color:{text_color};">{price}</td>'
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
            f'<a href="{video_url}" target="_blank" style="display:block;text-decoration:none;">'
            f'<img src="{thumbnail_url}" width="100%" alt="Watch video"'
            f' style="display:block;max-width:100%;height:auto;border:0;'
            f'border-radius:{border_radius};" />'
            f'</a>'
        )
        if caption:
            html += (
                f'<p style="margin:8px 0 0;font-family:Arial,sans-serif;font-size:13px;'
                f'color:#6b7280;text-align:center;">'
                f'<a href="{video_url}" target="_blank" style="color:#111827;font-weight:600;text-decoration:none;">'
                f'&#9654; {caption}</a></p>'
            )
        html += f'</td></tr></table>'
        return _spacing_wrapper(html, p)
