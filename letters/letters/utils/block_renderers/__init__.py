"""Email block renderers.

Each block type maps to a `BlockRenderer` that emits inbox-safe table HTML.
This package re-exports the full public surface so existing imports of
`letters.letters.utils.block_renderers` keep working unchanged.
"""

from .base import (
    BlockRenderer,
    _abs_image_src,
    _aspect_ref_width,
    _class_attr,
    _font_scale_class,
    _pad_class,
    _padding,
    _safe_url,
    _spacing_wrapper,
)
from .interactive import ButtonRenderer, LinkListRenderer
from .layout import ColumnsRenderer, ContainerRenderer, DividerRenderer, SpacerRenderer
from .media import ImageRenderer, ImageTextRenderer, ProductCardRenderer, VideoThumbRenderer
from .registry import RENDERER_MAP
from .rich_text import RichTextRenderer, _sanitize_rich_html
from .social import SocialRenderer
from .text import (
    FooterRenderer,
    HeaderRenderer,
    HeroRenderer,
    QuoteRenderer,
    SectionLabelRenderer,
)

__all__ = [
    "RENDERER_MAP",
    "BlockRenderer",
    "_safe_url",
    "_abs_image_src",
    "_padding",
    "_spacing_wrapper",
    "_sanitize_rich_html",
    "_font_scale_class",
    "_aspect_ref_width",
    "_pad_class",
    "_class_attr",
    "HeroRenderer",
    "SectionLabelRenderer",
    "RichTextRenderer",
    "ImageRenderer",
    "ImageTextRenderer",
    "ButtonRenderer",
    "ColumnsRenderer",
    "ContainerRenderer",
    "DividerRenderer",
    "FooterRenderer",
    "SpacerRenderer",
    "QuoteRenderer",
    "SocialRenderer",
    "ProductCardRenderer",
    "VideoThumbRenderer",
    "HeaderRenderer",
    "LinkListRenderer",
]
