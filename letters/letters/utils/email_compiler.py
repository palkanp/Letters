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
<meta name="color-scheme" content="light dark" />
<meta name="supported-color-schemes" content="light dark" />{font_links}
<style type="text/css">
@media (prefers-color-scheme: dark) {{
  body, .body-wrap {{ background-color:#1f2124 !important; }}
}}
@media only screen and (max-width:600px) {{
  .ltr-stack {{ display:block !important; width:100% !important; max-width:100% !important;
                padding-left:0 !important; padding-right:0 !important;
                border-right:0 !important; box-sizing:border-box !important; }}
  .ltr-stack-2 {{ display:inline-block !important; width:50% !important; max-width:50% !important;
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
<tr><td align="center" style="padding:24px 0;">
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
