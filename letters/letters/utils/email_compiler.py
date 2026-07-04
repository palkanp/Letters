from __future__ import annotations

from html import escape
from typing import Any

from .design_tree_processor import DesignTreeProcessor
from .block_renderers import RENDERER_MAP
from .fonts import google_fonts_link_tags

_HTML_WRAPPER = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<meta http-equiv="X-UA-Compatible" content="IE=edge" />
<meta name="color-scheme" content="light only" />
<meta name="supported-color-schemes" content="light only" />{font_links}
<style type="text/css">
/* Keep this <style> lean and standards-clean: Gmail drops ALL embedded styles
   (including the responsive media queries below) if it chokes on anything here,
   so colour-scheme lives only in the head meta tags above, not in a CSS rule. */
/* Columns are side-by-side table cells by default. Below the breakpoint —
   phones — stack them to full width and flip the divider from a full-height
   vertical rule to a horizontal one. Works in Gmail now that the send path no
   longer injects Frappe's email CSS (which was making Gmail drop these rules). */
@media only screen and (max-width:{col_breakpoint}px) {{
  .ltr-row {{ display:block !important; width:100% !important; }}
  .ltr-col-2up, .ltr-col-3up, .ltr-col-4up {{ display:block !important;
                 width:100% !important; padding-left:0 !important;
                 padding-right:0 !important; box-sizing:border-box !important; }}
  .ltr-coldiv {{ border-left-width:0 !important; border-top-width:1px !important;
                 margin-top:20px !important; padding-top:20px !important; }}
}}
@media only screen and (max-width:{email_width}px) {{
  .ltr-stack {{ display:block !important; width:100% !important; max-width:100% !important;
                padding-left:0 !important; padding-right:0 !important;
                border-right:0 !important; box-sizing:border-box !important; }}
  .ltr-stack-2 {{ display:inline-block !important; width:50% !important; max-width:50% !important;
                  vertical-align:top !important;
                  border-right:0 !important; box-sizing:border-box !important; }}
  .ltr-vdivider {{ display:block !important; width:100% !important; max-width:100% !important;
                    box-sizing:border-box !important; }}
  .ltr-vdivider table {{ width:100% !important; }}
  .ltr-vdivider td {{ width:100% !important; padding:12px 0 !important; text-align:left !important;
                       box-sizing:border-box !important; }}
  .ltr-vdivider div {{ display:block !important; width:100% !important; height:1px !important; }}
  .ltr-pad-x {{ padding-left:20px !important; padding-right:20px !important; }}
  .ltr-fs-xl {{ font-size:26px !important; line-height:1.25 !important; }}
  .ltr-fs-lg {{ font-size:21px !important; line-height:1.3 !important; }}
}}
</style>
</head>
<body style="margin:0;padding:0;background-color:#f3f4f6;">
{preheader}
<table class="body-wrap" width="100%" cellpadding="0" cellspacing="0" border="0"
       style="background-color:#f3f4f6;">
<tr><td align="center" style="padding:24px 16px;">
<table class="email-card" width="100%" cellpadding="0" cellspacing="0" border="0"
       style="background-color:#ffffff;border-radius:4px;overflow:hidden;max-width:{email_width}px;width:100%;">
<tr><td style="font-size:0;line-height:0;">{blocks}</td></tr>
</table>
</td></tr>
</table>
<!--email_open_check-->
</body>
</html>"""


class EmailCompiler:
    """Converts a validated block tree to email-safe HTML (no external dependencies)."""

    def __init__(self, blocks_json: str | list, preview_text: str = "", email_width: int = 600):
        self._processor = DesignTreeProcessor(blocks_json)
        self._preview_text = preview_text or ""
        self._email_width = int(email_width) if email_width else 600

    def compile(self) -> str:
        self._processor.validate()
        tree = self._processor.get_tree()
        blocks_html = self._render_blocks(tree)
        font_links = self._render_font_links(tree)
        return _HTML_WRAPPER.format(
            blocks=blocks_html,
            preheader=self._render_preheader(),
            email_width=self._email_width,
            # Columns stack below a phone-scale width and stay 2-up above it —
            # true responsive behaviour that now works in Gmail too, once the
            # send path stops injecting Frappe's email CSS (which made Gmail drop
            # all embedded styles). Well below the email width so desktop reading
            # panes (Gmail's included) keep the 2-column layout.
            col_breakpoint=min(self._email_width - 40, 480),
            font_links="\n" + font_links if font_links else "",
        )

    def _collect_fonts(self, blocks: list[dict[str, Any]]) -> list[str]:
        """Recursively collect all font_family values from the block tree."""
        fonts: list[str] = []
        for block in blocks:
            props = block.get("props") or {}
            if props.get("font_family"):
                fonts.append(props["font_family"])
            children = block.get("children") or []
            fonts.extend(self._collect_fonts(children))
        return fonts

    def _render_font_links(self, tree: list[dict[str, Any]]) -> str:
        fonts = self._collect_fonts(tree)
        return google_fonts_link_tags(fonts)

    def _render_preheader(self) -> str:
        """Hidden inbox preview line, shown in the inbox list, not in the email body."""
        if not self._preview_text:
            return ""
        return (
            '<div style="display:none;max-height:0;overflow:hidden;'
            'mso-hide:all;font-size:1px;line-height:1px;color:#f3f4f6;">'
            f"{escape(self._preview_text)}"
            "</div>"
        )

    def _render_blocks(self, tree: list[dict[str, Any]]) -> str:
        parts = []
        for block in tree:
            renderer = RENDERER_MAP.get(block["type"])
            if renderer:
                parts.append(renderer.render(block))
        return "".join(parts)
