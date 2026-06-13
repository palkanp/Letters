from .base import BlockRenderer
from .interactive import ButtonRenderer, LinkListRenderer
from .layout import ColumnsRenderer, ContainerRenderer, DividerRenderer, SpacerRenderer
from .media import ImageRenderer, ImageTextRenderer, ProductCardRenderer, VideoThumbRenderer
from .rich_text import RichTextRenderer
from .social import SocialRenderer
from .text import (
    FooterRenderer,
    HeaderRenderer,
    HeroRenderer,
    QuoteRenderer,
    SectionLabelRenderer,
)

# Maps a block's `type` to the singleton renderer that emits its email HTML.
RENDERER_MAP: dict[str, BlockRenderer] = {
    "hero":          HeroRenderer(),
    "section_label": SectionLabelRenderer(),
    "text":          RichTextRenderer(),
    "image":         ImageRenderer(),
    "image_text":    ImageTextRenderer(),
    "button":        ButtonRenderer(),
    "columns":       ColumnsRenderer(),
    "container":     ContainerRenderer(),
    "divider":       DividerRenderer(),
    "footer":        FooterRenderer(),
    "spacer":        SpacerRenderer(),
    "quote":         QuoteRenderer(),
    "social":        SocialRenderer(),
    "product_card":  ProductCardRenderer(),
    "video_thumb":   VideoThumbRenderer(),
    "header":        HeaderRenderer(),
    "rich_text":     RichTextRenderer(),
    "link_list":     LinkListRenderer(),
}
