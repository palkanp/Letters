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


def _font_scale_class(size: str) -> str:
    """Return a mobile shrink class for large fixed font sizes, else "".

    Big desktop headings (>=24px) stay oversized on phones because the size is
    baked inline. These classes let the head <style> media query scale them down
    on narrow screens. See email_compiler._HTML_WRAPPER.
    """
    try:
        px = int(str(size).replace("px", "").strip())
    except (ValueError, TypeError):
        return ""
    if px >= 32:
        return "ltr-fs-xl"
    if px >= 24:
        return "ltr-fs-lg"
    return ""


def _pad_class(props: dict, dl: int = 16, dr: int = 16, threshold: int = 30) -> str:
    """Return the "ltr-pad-x" mobile hint when a block's side padding is wide
    enough to crowd a phone screen, else "".

    Only horizontal padding is trimmed on mobile (the head media query drops it
    to 20px); vertical padding is left alone since vertical space costs nothing
    on a scrolling phone. `dl`/`dr` mirror the defaults each renderer passes to
    `_padding` so an unset value is judged against what actually renders.
    """
    l = int(props.get("padding_left",  dl))
    r = int(props.get("padding_right", dr))
    return "ltr-pad-x" if max(l, r) >= threshold else ""


def _class_attr(*tokens: str) -> str:
    """Join non-empty class tokens into a ` class="..."` attribute, or "" if none."""
    cls = " ".join(t for t in tokens if t)
    return f' class="{cls}"' if cls else ""


def _aspect_ref_width(image_width: str, ref: int = 600) -> int:
    """Approx. desktop pixel width of an image, used to build a stable aspect-ratio.

    Percent widths are resolved against the standard 600px email body so a
    `cover` image keeps the same crop shape (not a frozen height) as it scales
    down on mobile. Pixel widths are used directly.
    """
    iw = (image_width or "").strip()
    if iw.endswith("px"):
        try:
            return max(int(iw[:-2]), 1)
        except ValueError:
            return ref
    if iw.endswith("%"):
        try:
            return max(round(ref * int(iw[:-1]) / 100), 1)
        except ValueError:
            return ref
    return ref


def _padding(props: dict, dt: int = 20, dr: int = 16, db: int = 20, dl: int = 16) -> str:
    """Return a CSS padding shorthand from block props, falling back to supplied defaults."""
    t = int(props.get("padding_top",    dt))
    r = int(props.get("padding_right",  dr))
    b = int(props.get("padding_bottom", db))
    l = int(props.get("padding_left",   dl))
    return f"{t}px {r}px {b}px {l}px"


def _spacing_wrapper(inner_html: str, props: dict) -> str:
    """Wrap a block's HTML in a spacing table when explicit spacing is set.

    Each renderer already applies its own background-color directly on its
    outermost table. Wrapping again with the same bg when spacing is zero
    creates redundant nested tables that can produce sub-pixel seams between
    consecutive dark-background sections in scaled previews (e.g. Arc template
    thumbnail). Only wrap when there is actual non-zero spacing.
    """
    top    = int(props.get("spacing_top",    0))
    bottom = int(props.get("spacing_bottom", 0))
    left   = int(props.get("spacing_left",   0))
    right  = int(props.get("spacing_right",  0))
    if top == 0 and bottom == 0 and left == 0 and right == 0:
        return inner_html
    bg       = props.get("background_color", "")
    bg_style = f"background-color:{bg};" if bg and bg not in ("transparent", "") else ""
    padding  = f"padding:{top}px {right}px {bottom}px {left}px;"
    # Wide left/right spacing also crowds a phone; trim it on mobile like padding.
    pad_cls  = ' class="ltr-pad-x"' if max(left, right) >= 30 else ""
    return (
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0"'
        f' style="{bg_style}">'
        f'<tr><td{pad_cls} style="{padding}">'
        f'{inner_html}'
        f'</td></tr></table>'
    )


class BlockRenderer(ABC):
    @abstractmethod
    def render(self, block: dict[str, Any]) -> str:
        """Return email-safe HTML for this block."""
