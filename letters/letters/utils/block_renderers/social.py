from functools import lru_cache
from html import escape
from pathlib import Path
from typing import Any

from .base import BlockRenderer, _class_attr, _pad_class, _padding, _safe_css_value, _safe_url, _spacing_wrapper


def _platform_slug(label: str) -> str:
    return label.lower().replace(" / ", "-").replace(" ", "-")


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    """Parse a #rgb / #rrggbb color to an (r, g, b) tuple; fall back to slate."""
    h = color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except (ValueError, IndexError):
        return 0x37, 0x41, 0x51  # #374151, the social block default


def _tint_mask_png(platform: str, color: str, out_path: Path) -> None:
    """Write a color-tinted PNG of a social glyph by painting `color` through the
    pre-baked alpha mask shipped at images/social-masks/<platform>.png. Pillow is
    a core Frappe dependency, so this needs no runtime SVG rasterizer.
    """
    from PIL import Image
    import frappe

    mask_path = frappe.get_app_path(
        "letters", "public", "images", "social-masks", f"{platform}.png")
    alpha = Image.open(mask_path).convert("RGBA").getchannel("A")
    tinted = Image.new("RGBA", alpha.size, _hex_to_rgb(color) + (255,))
    tinted.putalpha(alpha)
    tinted.save(out_path, "PNG")


@lru_cache(maxsize=256)
def _social_icon_img(svg_path: str, color: str, label: str, size: int = 24) -> str:
    """Return an <img> tag for a social icon as a color-tinted PNG.

    Gmail/Outlook/Yahoo don't render SVG (or data-URI) <img> sources, so we serve
    a raster PNG: the glyph's pre-baked alpha mask tinted to the chosen color and
    hosted with an absolute URL. Written once per (platform, color) and cached in
    memory afterwards. Outside a Frappe runtime (unit tests) we fall back to a
    data-URI SVG so rendering still works there.
    """
    platform  = _platform_slug(label)
    color_key = color.lstrip("#").lower()
    filename  = f"{platform}-{color_key}.png"

    try:
        import frappe
        icons_dir = Path(frappe.get_site_path("public", "files", "social-icons"))
        icons_dir.mkdir(parents=True, exist_ok=True)
        icon_file = icons_dir / filename
        if not icon_file.exists():
            _tint_mask_png(platform, color, icon_file)
        from frappe.utils import get_url
        src = escape(get_url(f"/files/social-icons/{filename}"))
    except Exception:
        # Outside Frappe (unit tests / local dev without context) — data-URI SVG.
        from base64 import b64encode
        svg_content = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"'
            f' width="{size}" height="{size}">'
            f'<path fill="{color}" d="{svg_path}"/>'
            f'</svg>'
        )
        encoded = b64encode(svg_content.encode()).decode()
        src = f"data:image/svg+xml;base64,{encoded}"

    return (
        f'<img src="{src}"'
        f' width="{size}" height="{size}" alt="{label}"'
        f' style="display:block;border:0;">'
    )


# SVG paths from Simple Icons (https://simpleicons.org) — CC0 1.0 / brand guidelines apply
_SOCIAL_ICONS: dict[str, tuple[str, str]] = {
    "x_url": (
        "X / Twitter",
        "M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231"
        "-5.401 6.231H2.746l7.73-8.835L1.254 2.25H8.08l4.253 5.622zm"
        "-1.161 17.52h1.833L7.084 4.126H5.117z",
    ),
    "linkedin_url": (
        "LinkedIn",
        "M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037"
        "-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046"
        "c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286z"
        "M5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065z"
        "m1.782 13.019H3.555V9h3.564v11.452z"
        "M22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24"
        "h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z",
    ),
    "instagram_url": (
        "Instagram",
        "M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919"
        ".058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849"
        "-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07"
        "-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92"
        "-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849"
        ".149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069z"
        "M12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052"
        ".014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948"
        ".2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24"
        "c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98"
        ".059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947"
        "-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0z"
        "m0 5.838a6.162 6.162 0 1 0 0 12.324 6.162 6.162 0 0 0 0-12.324z"
        "M12 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm6.406-11.845a1.44 1.44 0 1 0 0 2.881 1.44 1.44 0 0 0 0-2.881z",
    ),
    "facebook_url": (
        "Facebook",
        "M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12"
        "c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43"
        "c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953"
        "H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796"
        "v8.385C19.612 23.027 24 18.062 24 12.073z",
    ),
    "youtube_url": (
        "YouTube",
        "M23.495 6.205a3.007 3.007 0 0 0-2.088-2.088c-1.87-.501-9.396-.501"
        "-9.396-.501s-7.507-.01-9.396.501A3.007 3.007 0 0 0 .527 6.205"
        "a31.247 31.247 0 0 0-.522 5.805 31.247 31.247 0 0 0 .522 5.783"
        "a3.007 3.007 0 0 0 2.088 2.088c1.868.502 9.396.502 9.396.502"
        "s7.506 0 9.396-.502a3.007 3.007 0 0 0 2.088-2.088"
        "a31.247 31.247 0 0 0 .5-5.783 31.247 31.247 0 0 0-.5-5.805z"
        "M9.609 15.601V8.408l6.264 3.602z",
    ),
    "github_url": (
        "GitHub",
        "M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385"
        ".6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04"
        "-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7"
        "c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236"
        "1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605"
        "-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22"
        "-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23"
        ".96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405"
        "2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176"
        ".765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92"
        ".42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315"
        ".21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12",
    ),
    "website_url": (
        "Website",
        "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"
        "m-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1"
        "c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3"
        "c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41"
        "c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z",
    ),
}


class SocialRenderer(BlockRenderer):
    def render(self, block: dict[str, Any]) -> str:
        p       = block.get("props", {})
        # Sanitized: color flows into an SVG fill attr *and* into the cached icon
        # filename (color.lstrip("#")), so an unsanitized "/" or ".." would allow
        # a path-traversal .svg write. The whitelist keeps hex/named colors.
        color   = _safe_css_value(p.get("color", "#374151")) or "#374151"
        bg      = _safe_css_value(p.get("background_color", "#ffffff"))
        align   = _safe_css_value(p.get("align", "center"))
        padding = _padding(p, 20, 16, 20, 16)
        icon_size = int(p.get("icon_size", 32))

        links = []
        for key, (label, svg_path) in _SOCIAL_ICONS.items():
            url = p.get(key, "").strip()
            if url:
                icon = _social_icon_img(svg_path, color, label, icon_size)
                links.append(
                    f'<a href="{_safe_url(url)}" style="display:inline-block;'
                    f'margin:4px;text-decoration:none;" title="{label}">'
                    f'{icon}</a>'
                )

        if not links:
            return ""

        pad_class = _class_attr(_pad_class(p))
        html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            f' style="background-color:{bg};">'
            f'<tr><td align="{align}"{pad_class} style="padding:{padding};">'
            + "".join(links) +
            f'</td></tr></table>'
        )
        return _spacing_wrapper(html, p)
