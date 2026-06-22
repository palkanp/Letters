from abc import ABC, abstractmethod
from html import escape
from typing import Any


def _safe_url(url: str) -> str:
    """Return an HTML-escaped URL, rejecting dangerous protocol schemes."""
    url = (url or "").strip()
    if url.lower().lstrip("\x00\t\n\r\f ").startswith(("javascript:", "data:", "vbscript:")):
        return "#"
    return escape(url)


def _abs_image_src(url: str) -> str:
    """Make an image src absolute and HTML-escape it.

    Uploaded files are stored as site-relative paths like "/files/x.png". Email
    clients have no base URL to resolve those against, so a relative src always
    renders as a broken image in the inbox. Prepend the site's public URL so the
    image loads. Already-absolute (http/https/protocol-relative/data) URLs and
    empty values are left untouched.
    """
    url = (url or "").strip()
    if not url or url.startswith(("http://", "https://", "//", "data:")):
        return escape(url)
    if url.startswith("/"):
        try:
            from frappe.utils import get_url
            return escape(get_url(url))
        except Exception:
            # Outside a Frappe runtime (e.g. unit tests) leave it relative.
            return escape(url)
    return escape(url)


def _padding(props: dict, dt: int = 20, dr: int = 16, db: int = 20, dl: int = 16) -> str:
    """Return a CSS padding shorthand from block props, falling back to supplied defaults."""
    t = int(props.get("padding_top",    dt))
    r = int(props.get("padding_right",  dr))
    b = int(props.get("padding_bottom", db))
    l = int(props.get("padding_left",   dl))
    return f"{t}px {r}px {b}px {l}px"


def _spacing_wrapper(inner_html: str, props: dict) -> str:
    """Wrap a block's HTML in a table row that applies spacing and background color."""
    top    = int(props.get("spacing_top", 0))
    bottom = int(props.get("spacing_bottom", 0))
    left   = int(props.get("spacing_left", 0))
    right  = int(props.get("spacing_right", 0))
    bg     = props.get("background_color", "")
    bg_style = f"background-color:{bg};" if bg and bg not in ("transparent", "") else ""
    if top == 0 and bottom == 0 and left == 0 and right == 0 and not bg_style:
        return inner_html
    padding = f"padding:{top}px {right}px {bottom}px {left}px;"
    return (
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
        f' style="{bg_style}">'
        f'<tr><td style="{padding}">'
        f'{inner_html}'
        f'</td></tr></table>'
    )


class BlockRenderer(ABC):
    @abstractmethod
    def render(self, block: dict[str, Any]) -> str:
        """Return email-safe HTML for this block."""
