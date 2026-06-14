"""Generate the brand-logo PNGs used by the starter templates.

We host the logos as PNG because Gmail strips data-URI and SVG <img>s, so a
hosted raster is the only email-safe option. Each mark is an accent rounded
square with a glyph + a wordmark, drawn on a 600x50 LOGICAL board (rendered at
3x for crisp edges, then the image block's width:100% renders it 1:1 at the
600px card width). Keep BRANDS in sync with the logo(T, "<slug>") calls in
build_templates.py.

    python3 scripts/gen_logos.py            # write every brand
    python3 scripts/gen_logos.py relay      # write one brand

Requires Pillow (dev-time only — not a runtime dependency).
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "letters", "public", "images", "logos")
SCALE = 3                 # supersample for crisp text, downscaled at the end
W, H = 600, 50            # logical board (matches logo() in build_templates.py)

_FONTS = {
    "sans":  "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "serif": "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
}

# One entry per brand; slug is the output filename and the logo() argument.
BRANDS = {
    "relay": {"name": "Relay", "glyph": "R", "accent": "#4F46E5", "ink": "#16181D", "font": "sans"},
}


def _font(kind, size):
    return ImageFont.truetype(_FONTS[kind], size * SCALE)


def make_logo(slug, name, glyph, accent, ink, font):
    img = Image.new("RGBA", (W * SCALE, H * SCALE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    word_font = _font(font, 20)
    glyph_font = _font(font, 17)
    sq = 30 * SCALE
    gap = 12 * SCALE

    # measure the wordmark to centre the [square | gap | word] group
    l, t, r, b = d.textbbox((0, 0), name, font=word_font)
    text_w = r - l
    group_w = sq + gap + text_w
    x0 = (W * SCALE - group_w) / 2
    cy = H * SCALE / 2

    # accent rounded square
    ry = cy - sq / 2
    d.rounded_rectangle([x0, ry, x0 + sq, ry + sq], radius=8 * SCALE, fill=accent)

    # glyph centred in the square
    d.text((x0 + sq / 2, cy), glyph, font=glyph_font, fill="#ffffff", anchor="mm")

    # wordmark, vertically centred against its own cap/baseline box
    lw, tw_, rw, bw = d.textbbox((0, 0), name, font=word_font)
    d.text((x0 + sq + gap, cy - (tw_ + bw) / 2), name, font=word_font, fill=ink)

    img = img.resize((W, H), Image.LANCZOS)
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"{slug}.png")
    img.save(path)
    print(f"wrote {slug}.png")


def main():
    wanted = sys.argv[1:] or list(BRANDS)
    for slug in wanted:
        make_logo(slug, **BRANDS[slug])


if __name__ == "__main__":
    main()
