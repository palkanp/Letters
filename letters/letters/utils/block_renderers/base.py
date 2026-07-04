import re
from abc import ABC, abstractmethod
from html import escape
from typing import Any

_CSS_VALUE_RE = re.compile(r"^[#a-zA-Z0-9%.,\-\s]*$")


def _safe_css_value(value: Any) -> str:
    """Constrain a CSS value (color, size, font-weight, alignment, spacing) to
    a safe character set before it is interpolated into a style="" attribute.

    HTML-escaping alone does not stop CSS-declaration injection: `;` and `(`
    aren't special to HTML, so an attacker-controlled color/size prop could
    append extra declarations (e.g. `red;background:url(https://evil/track.gif)`)
    that `html.escape` lets straight through. Anything outside the whitelist
    (hex colors, alphanumerics, `%`, `.`, `,`, `-`, spaces) is dropped rather
    than passed through, which only costs that one declaration.
    """
    v = str(value or "").strip()
    return v if _CSS_VALUE_RE.match(v) else ""


_URL_SCHEME_NOISE_RE = re.compile(r"[\x00-\x20]")


def _safe_url(url: str) -> str:
    """Return an HTML-escaped URL, rejecting dangerous protocol schemes."""
    url = (url or "").strip()
    # Browsers ignore control chars and whitespace *anywhere* in the scheme
    # (e.g. `java\tscript:` or `java\nscript:`), so strip them across the whole
    # string before the check — lstrip alone only catches leading ones.
    probe = _URL_SCHEME_NOISE_RE.sub("", url).lower()
    if probe.startswith(("javascript:", "data:", "vbscript:")):
        return "#"
    return escape(url)


_SVG_EXT_RE = re.compile(r"\.svg(?:[?#]|$)", re.IGNORECASE)


def _is_svg_src(url: str) -> bool:
    """Best-effort check for an SVG image by file extension.

    We can't inspect the real content-type of an arbitrary hotlinked URL without
    fetching it server-side (an SSRF risk we don't want to take on), so this is
    an extension match, not a content sniff. Good enough to catch the common
    case: an upload or pasted link ending in .svg (optionally followed by a
    query string or fragment).
    """
    return bool(_SVG_EXT_RE.search((url or "").strip()))


_PRIVATE_FILE_RE = re.compile(r"/private/files/", re.IGNORECASE)


def _is_private_file_src(url: str) -> bool:
    """True if the URL points at a Frappe private file (/private/files/...).

    Private files require an authenticated site session to view, so an <img>
    pointed at one is guaranteed broken for every recipient who isn't logged
    into this site — the same failure class as an SVG source, just from access
    control rather than client format support. Path-shape check only (Frappe's
    own public/private URL convention), no DB lookup or fetch involved.
    """
    return bool(_PRIVATE_FILE_RE.search((url or "").strip()))


def _abs_image_src(url: str) -> str:
    """Make an image src absolute and HTML-escape it.

    Uploaded files are stored as site-relative paths like "/files/x.png". Email
    clients have no base URL to resolve those against, so a relative src always
    renders as a broken image in the inbox. Prepend the site's public URL so the
    image loads. Already-absolute (http/https/protocol-relative/data) URLs and
    empty values are left untouched.

    SVG sources and private-file sources are dropped entirely (returns "")
    regardless of how the URL got into the block — upload, pasted link, or
    fixture — because both are guaranteed broken for real recipients: Gmail,
    Outlook, and Yahoo all fail to render SVG <img> sources (only Apple Mail
    does), and a private file 403s for anyone not logged into this site. This
    is the single choke point every renderer routes image/thumbnail/logo URLs
    through, so this guard covers all of them.
    """
    url = (url or "").strip()
    if not url:
        return ""
    if _is_svg_src(url) or _is_private_file_src(url):
        return ""
    if url.startswith(("http://", "https://", "//", "data:")):
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
    bg       = _safe_css_value(props.get("background_color", ""))
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
