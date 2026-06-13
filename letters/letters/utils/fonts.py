"""Font definitions — single source of truth for the renderer.

Mirrors frontend/src/fonts.js exactly; keep the two in sync.

Two categories:
  - System fonts: email-safe, no <link> needed, only 400/700 available.
  - Web fonts:    loaded from Google Fonts, support 400/500/600/700.
                  Clients that don't support web fonts (Outlook on Windows)
                  silently fall back to the system fallback stack.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# System fonts (email-safe, 400 + 700 only)
# ---------------------------------------------------------------------------

_SYSTEM_FONT_STACKS: dict[str, str] = {
    # Sans-serif
    "Arial":           "Arial, Helvetica, sans-serif",
    "Helvetica":       "Helvetica, Arial, sans-serif",
    "Verdana":         "Verdana, Geneva, sans-serif",
    "Tahoma":          "Tahoma, Geneva, sans-serif",
    "Trebuchet MS":    "'Trebuchet MS', Helvetica, sans-serif",
    # Serif
    "Georgia":         "Georgia, 'Times New Roman', serif",
    "Times New Roman": "'Times New Roman', Times, serif",
    # Monospace
    "Courier New":     "'Courier New', Courier, monospace",
}

# ---------------------------------------------------------------------------
# Web fonts (Google Fonts, 400/500/600/700)
# ---------------------------------------------------------------------------
# weights: only variants the typeface actually ships (requesting a missing
# weight causes browsers/email clients to fake-bold or fake-oblique).
#
# Email client support:
#   ✅ Apple Mail (macOS/iOS), Gmail (web/Android/iOS), Outlook (Mac),
#      Samsung Mail, Yahoo Mail, Fastmail
#   ❌ Outlook on Windows (2016–365) — falls back to the system stack

WEB_FONT_META: dict[str, dict] = {
    "Inter":     {"google_family": "Inter",     "weights": [400, 500, 600, 700], "fallback": "Arial, Helvetica, sans-serif"},
    "Roboto":    {"google_family": "Roboto",    "weights": [400, 500, 700],      "fallback": "Arial, Helvetica, sans-serif"},
    "Open Sans": {"google_family": "Open+Sans", "weights": [400, 500, 600, 700], "fallback": "Arial, Helvetica, sans-serif"},
    "Poppins":   {"google_family": "Poppins",   "weights": [400, 500, 600, 700], "fallback": "Arial, Helvetica, sans-serif"},
}

# ---------------------------------------------------------------------------
# Combined stack map
# ---------------------------------------------------------------------------

FONT_STACKS: dict[str, str] = {
    **_SYSTEM_FONT_STACKS,
    **{name: f"'{name}', {meta['fallback']}" for name, meta in WEB_FONT_META.items()},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def font_stack(props: dict, fallback: str) -> str:
    """Resolve a block's font_family prop to a full CSS stack.

    Unknown / empty names return ``fallback`` unchanged so blocks saved before
    this feature render exactly as before.
    """
    name = (props.get("font_family") or "").strip()
    return FONT_STACKS.get(name, fallback)


def is_web_font(name: str) -> bool:
    """Return True if the name refers to a Google Fonts web font."""
    return (name or "").strip() in WEB_FONT_META


def google_fonts_url(names: list[str]) -> str | None:
    """Build a Google Fonts stylesheet URL for the given font names.

    System font names are ignored. Returns None if none of the names are
    web fonts.
    """
    seen: set[str] = set()
    families: list[str] = []
    for name in (names or []):
        name = (name or "").strip()
        if name in WEB_FONT_META and name not in seen:
            seen.add(name)
            families.append(name)

    if not families:
        return None

    parts = []
    for name in families:
        meta = WEB_FONT_META[name]
        weights = ";".join(str(w) for w in meta["weights"])
        parts.append(f"family={meta['google_family']}:wght@{weights}")

    return f"https://fonts.googleapis.com/css2?{'&'.join(parts)}&display=swap"


def google_fonts_link_tags(names: list[str]) -> str:
    """Return HTML <link> tags for the web fonts in ``names``, or empty string."""
    url = google_fonts_url(names)
    if not url:
        return ""
    return (
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        f'<link rel="stylesheet" href="{url}">'
    )
