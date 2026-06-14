"""Builds the Letters starter templates.

Each template is a plain list of block dicts (readable here, serialized to the
blocks_json string the fixtures store). Run with plain python3 — the email
compiler renders standalone; `/assets/...` image paths stay relative and resolve
in the browser when served from the Frappe site.

    python3 scripts/build_templates.py            # write preview HTML
    python3 scripts/build_templates.py --fixtures # also rewrite the fixtures

Style is borrowed from Frappe Builder's template hub (palettes, spacing, copy
voice, fictional businesses like Relay/Northwind), but rendered with OUR fonts
only — Inter for product/SaaS, Georgia for warm/editorial. See the
builder-design-system memory note.

Type discipline (one voice per template):
  • One font family. Two weights (400 body / 700 headings). A small size scale.
  • Two ink colours (heading ink + muted body); the accent is reserved for
    interactive things (wordmark, links, buttons) and the eyebrow.
  • No all-caps, no letter-spacing tricks. Banners/standalone lines centred,
    paragraphs left, emphasis is <strong> (same size, same colour).
  • One primary CTA per template — showcase cards carry no competing button.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from letters.letters.utils.email_compiler import EmailCompiler

# Images are hot-linked from Unsplash (same approach Frappe Builder uses) rather
# than self-hosted in the app. The "?auto=format&fit=crop&q=80&w=NNNN" query is
# Builder's exact format — Unsplash serves an optimised, cropped JPEG.
def unsplash(photo_id, w=1200):
    return f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&q=80&w={w}"


SIDE = 44  # generous, consistent side padding on the 600px card


class Theme:
    def __init__(self, font, ink, body, accent, accent_soft, surface, border):
        self.font, self.ink, self.body, self.accent = font, ink, body, accent
        self.accent_soft, self.surface, self.border = accent_soft, surface, border


# ── block helpers (one type role each) ───────────────────────────────────────

LOGO_DIR = "/assets/letters/images/logos/"


def logo(T, slug, *, bg="#ffffff", pt=30, pb=10):
    """Builder-style brand mark: an accent rounded-square glyph + wordmark,
    served as a hosted PNG (email-safe — unlike data-URI/SVG images, which Gmail
    strips). The PNG is a 600x50 logical canvas with the mark centered, so the
    image block's width:100% renders it 1:1 at 600px and proportionally below;
    the mark never balloons the way a normal image would.

    Generate the PNG with scripts/gen_logos.js (run in the preview browser);
    files land in letters/public/images/logos/<slug>.png."""
    return {"type": "image", "props": {
        "image_url": LOGO_DIR + slug + ".png", "border": "none",
        "border_radius": "0", "background_color": bg, "alt": slug.title(),
        "padding_top": pt, "padding_bottom": pb, "padding_left": SIDE, "padding_right": SIDE}}


def wordmark(T, name, *, bg="#ffffff"):
    """Quiet text wordmark in the accent — for warm/serif brands where a glyph
    box would feel too techy."""
    return {"type": "text", "props": {
        "html_content": f"<p>{name}</p>", "align": "center", "font_family": T.font,
        "font_size": "17px", "font_weight": "700", "text_color": T.accent,
        "background_color": bg,
        "padding_top": 30, "padding_bottom": 8, "padding_left": SIDE, "padding_right": SIDE}}


def eyebrow(T, label, *, bg="#ffffff", pt=40):
    """Builder's small accent eyebrow above the headline (in lieu of a pill)."""
    return {"type": "text", "props": {
        "html_content": f"<p>{label}</p>", "align": "center", "font_family": T.font,
        "font_size": "14px", "font_weight": "700", "text_color": T.accent,
        "background_color": bg, "padding_top": pt, "padding_bottom": 0,
        "padding_left": SIDE, "padding_right": SIDE}}


def headline(T, html, *, bg="#ffffff", size="30px", pt=12, pb=10):
    """Big bold centred heading — the hero line. Two-part headings welcome."""
    return {"type": "text", "props": {
        "html_content": html, "align": "center", "font_family": T.font,
        "font_size": size, "font_weight": "700", "text_color": T.ink, "line_height": "1.25",
        "background_color": bg, "padding_top": pt, "padding_bottom": pb,
        "padding_left": SIDE, "padding_right": SIDE}}


def lead(T, html, *, bg="#ffffff", pt=6, pb=36):
    """Muted centred sub-headline under the hero line."""
    return {"type": "text", "props": {
        "html_content": html, "align": "center", "font_family": T.font,
        "font_size": "17px", "font_weight": "400", "text_color": T.body, "line_height": "1.6",
        "background_color": bg, "padding_top": pt, "padding_bottom": pb,
        "padding_left": SIDE, "padding_right": SIDE}}


def heading(T, title, *, bg="#ffffff", pt=32, pb=8):
    """Left-aligned section heading — 18/700/ink."""
    return {"type": "text", "props": {
        "html_content": f"<p>{title}</p>", "align": "left", "font_family": T.font,
        "font_size": "18px", "font_weight": "700", "text_color": T.ink, "line_height": "1.4",
        "background_color": bg, "padding_top": pt, "padding_bottom": pb,
        "padding_left": SIDE, "padding_right": SIDE}}


def body(T, html, *, align="left", color=None, bg="#ffffff", pt=12, pb=12):
    return {"type": "text", "props": {
        "html_content": html, "align": align, "font_family": T.font,
        "font_size": "16px", "font_weight": "400", "text_color": color or T.body, "line_height": "1.7",
        "background_color": bg, "padding_top": pt, "padding_bottom": pb,
        "padding_left": SIDE, "padding_right": SIDE}}


def image(T, url, *, bg="#ffffff", pt=8, pb=8, radius="10px", pl=None, pr=None):
    # 10px is Builder's dominant image radius across the Relay/Commit templates.
    return {"type": "image", "props": {
        "image_url": url, "border": "none", "border_radius": radius,
        "background_color": bg, "padding_top": pt, "padding_bottom": pb,
        "padding_left": SIDE if pl is None else pl,
        "padding_right": SIDE if pr is None else pr}}


def stats(T, items, *, bg="#ffffff", pt=16, pb=16):
    """Social-proof row: accent numbers + muted labels as equal columns."""
    columns = []
    for number, label in items:
        columns.append({"blocks": [
            {"type": "text", "props": {
                "html_content": f"<p>{number}</p>", "align": "center", "font_family": T.font,
                "font_size": "20px", "font_weight": "700", "text_color": T.accent,
                "line_height": "1.2", "padding_top": 0, "padding_bottom": 4,
                "padding_left": 4, "padding_right": 4}},
            {"type": "text", "props": {
                "html_content": f"<p>{label}</p>", "align": "center", "font_family": T.font,
                "font_size": "13px", "font_weight": "400", "text_color": T.body,
                "line_height": "1.4", "padding_top": 0, "padding_bottom": 0,
                "padding_left": 4, "padding_right": 4}}]})
    return {"type": "columns", "columns": columns, "props": {
        "background_color": bg, "col_gap": 8,
        "padding_top": pt, "padding_bottom": pb, "padding_left": SIDE, "padding_right": SIDE}}


def button(T, label, *, bg="#ffffff", pt=28, pb=52, size="normal"):
    return {"type": "button", "props": {
        "label": label, "url": "#", "color": T.accent, "text_color": "#ffffff",
        "background_color": bg, "font_family": T.font, "font_size": "15px",
        "button_padding": size, "border_radius": "999px",
        "align": "center", "padding_top": pt, "padding_bottom": pb}}


def links(T, items, *, bg="#ffffff", pt=4, pb=8):
    return {"type": "link_list", "props": {
        "items": items, "style": "none", "font_family": T.font,
        "link_color": T.accent, "text_color": T.body, "background_color": bg,
        "padding_top": pt, "padding_bottom": pb, "padding_left": SIDE, "padding_right": SIDE}}


def product(T, url, title, desc, price, btn=""):
    return {"type": "product_card", "props": {
        "image_url": url, "title": title, "description": desc, "price": price,
        "button_label": btn, "button_url": "#", "font_family": T.font,
        "button_color": T.accent, "title_color": T.ink, "text_color": T.body,
        "border_color": T.border, "border_radius": "14px",
        "padding_left": SIDE, "padding_right": SIDE}}


def divider(T, *, bg="#ffffff", pt=24, pb=8):
    return {"type": "divider", "props": {
        "border_color": T.border, "width": "100%", "padding_top": pt, "padding_bottom": pb,
        "background_color": bg, "padding_left": SIDE, "padding_right": SIDE}}


def social(T, *, bg="#ffffff"):
    return {"type": "social", "props": {
        "instagram_url": "https://instagram.com", "x_url": "https://x.com",
        "website_url": "https://example.com", "color": "#b8bec7", "align": "center",
        "icon_size": 16,
        "background_color": bg, "padding_top": 24, "padding_bottom": 8}}


def footer(T, txt, *, bg="#ffffff"):
    return {"type": "footer", "props": {
        "text": txt, "background_color": bg, "text_color": "#9ca3af",
        "font_family": T.font, "padding_top": 8, "padding_bottom": 20,
        "padding_left": SIDE, "padding_right": SIDE}}


def section_label(T, label, *, bg="#ffffff", align="left", pt=36):
    return {"type": "section_label", "props": {
        "label": label, "align": align, "font_family": T.font,
        "text_color": T.body, "line_color": T.border, "background_color": bg,
        "padding_top": pt, "padding_bottom": 6, "padding_left": SIDE, "padding_right": SIDE}}


def quote(T, text, author, role="", *, style="left-border", bg=None):
    return {"type": "quote", "props": {
        "quote": text, "author": author, "role": role, "style": style,
        "font_family": T.font, "quote_color": T.ink, "author_color": T.body,
        "border_color": T.accent, "background_color": bg or T.surface,
        "padding_top": 36, "padding_bottom": 36, "padding_left": SIDE, "padding_right": SIDE}}


def image_text(T, url, text, *, heading="", position="left", img_width="180px",
               bg="#ffffff", pt=24, pb=20):
    return {"type": "image_text", "props": {
        "image_url": url, "text": text, "heading": heading,
        "heading_color": T.ink, "image_position": position,
        "image_width": img_width, "font_family": T.font, "background_color": bg,
        "padding_top": pt, "padding_bottom": pb,
        "padding_left": SIDE, "padding_right": SIDE}}


def hero_block(T, heading, subheading, *, bg=None, size="32px", pt=52, pb=44):
    return {"type": "hero", "props": {
        "heading": heading, "subheading": subheading,
        "background_color": bg or T.surface, "heading_color": T.ink,
        "subheading_color": T.body, "heading_size": size, "font_family": T.font,
        "padding_top": pt, "padding_bottom": pb}}


def features(T, items, *, bg="#ffffff", pt=20, pb=24):
    """Three-column feature grid — title + description, no big number."""
    columns = []
    for title, desc in items:
        columns.append({"blocks": [
            {"type": "text", "props": {
                "html_content": f"<p>{title}</p>", "align": "left", "font_family": T.font,
                "font_size": "15px", "font_weight": "700", "text_color": T.ink,
                "line_height": "1.3", "padding_top": 0, "padding_bottom": 6,
                "padding_left": 0, "padding_right": 0}},
            {"type": "text", "props": {
                "html_content": f"<p>{desc}</p>", "align": "left", "font_family": T.font,
                "font_size": "13px", "font_weight": "400", "text_color": T.body,
                "line_height": "1.6", "padding_top": 0, "padding_bottom": 0,
                "padding_left": 0, "padding_right": 0}}]})
    return {"type": "columns", "columns": columns, "props": {
        "background_color": bg, "col_gap": 20,
        "padding_top": pt, "padding_bottom": pb, "padding_left": SIDE, "padding_right": SIDE}}


# ── Template: Welcome & Onboarding — "Relay" (Builder's SaaS business) ────────
# Copies Builder's Relay theme (indigo #4F46E5 on white, Inter, pill buttons,
# punchy two-part voice) and its actual product story ("fast teams stay in
# sync"). Focus: first success + the docs/videos that help.

RELAY = Theme(font="Inter", ink="#16181D", body="#6A7080", accent="#4F46E5",
              accent_soft="#EEF2FF", surface="#F6F7F9", border="#E5E7EC")

welcome_relay = [
    wordmark(RELAY, "Relay"),
    eyebrow(RELAY, "Your workspace is ready"),
    headline(RELAY, "<p>Welcome to Relay.</p>"),
    lead(RELAY, "<p>Your team's daily digest is one setup away.</p>"),
    image(RELAY, unsplash("photo-1551288049-bebda4e38f71", 1200), pt=4, pb=8),
    body(RELAY, "<p>Hi there,</p><p>Glad you're here. You're about ninety seconds from "
                "your first digest — here's the quickest path to it.</p>"),
    heading(RELAY, "Get set up in three steps"),
    body(RELAY, "<ol><li>Connect your tools — most teams start with GitHub and Slack.</li>"
                "<li>Invite a teammate or two, so the digest has a room to land in.</li>"
                "<li>Set your digest time and let Relay handle the rest.</li></ol>", pt=0),
    button(RELAY, "Open Relay →"),
    stats(RELAY, [("4,200+", "Teams on Relay"), ("31%", "Fewer meetings"),
                  ("99.99%", "Uptime")], bg=RELAY.surface, pt=24, pb=24),
    heading(RELAY, "Learn the essentials", pt=48),
    links(RELAY, [
        {"title": "Read the quickstart guide", "url": "#", "description": "Ten minutes from connect to your first digest."},
        {"title": "Watch the 3-minute tour", "url": "#", "description": "See threads, digests, and decisions in action."},
        {"title": "Take the Relay Academy course", "url": "#", "description": "A short, free course on running calmer teams."}],
         pt=24, pb=24),
    social(RELAY, bg=RELAY.surface),
    footer(RELAY, "You're receiving this because you created a Relay workspace. "
                  "Manage your email preferences or unsubscribe anytime.", bg=RELAY.surface),
]


# ── Template: Promotional Offer — "Wovenly" (knitwear apparel) — APPROVED ─────

WOVENLY = Theme(font="Georgia", ink="#3f3a34", body="#6b6258", accent="#b15a3c",
                accent_soft="#f7f3ee", surface="#f7f3ee", border="#ece7e1")
WOVENLY.band = "#f1e7da"

promo_wovenly = [
    wordmark(WOVENLY, "Wovenly"),
    headline(WOVENLY, "<p>The End-of-Season Edit</p>", bg=WOVENLY.accent_soft, size="32px", pt=20),
    lead(WOVENLY, "<p>The knitwear you keep reaching for, now softer on the price.</p>",
         bg=WOVENLY.accent_soft),
    image(WOVENLY, unsplash("photo-1620799140408-edc6dcb6d633", 1200)),
    body(WOVENLY, "<p>Take 25% off everything knit — applied automatically with code "
                  "<strong>SOFT25</strong>.</p>", align="center",
         bg=WOVENLY.band, pt=22, pb=22),
    body(WOVENLY, "<p>Cooler evenings call for softer layers. We've marked down the whole "
                  "knit collection — the oversized cardigans, the fringe ponchos, the merino "
                  "crews you keep reaching for. A few favourites to start with:</p>", pt=20),
    product(WOVENLY, unsplash("photo-1434389677669-e08b4cac3105", 900) + "&h=600", "The Fringe Poncho",
            "Hand-finished open knit in undyed cotton. One size, endlessly layerable.",
            "$78  ·  was $104"),
    body(WOVENLY, "<p><strong>The sale ends Sunday at midnight.</strong></p>",
         align="center", color=WOVENLY.ink, pt=16, pb=4),
    button(WOVENLY, "Shop the sale →"),
    social(WOVENLY, bg=WOVENLY.accent_soft),
    footer(WOVENLY, "Free returns within 30 days · carbon-neutral shipping. You're receiving "
                    "this because you shopped with Wovenly or joined our list — unsubscribe anytime.",
           bg=WOVENLY.accent_soft),
]


# ── Template: Product Release — "Relay 2.0" ──────────────────────────────────
# Same Relay brand, but the voice shifts from onboarding warmth to confident
# product announcement. Leans on section_label to chunk the email, a three-col
# feature grid (columns) for what's new, and a left-border quote for social
# proof before the CTA.

release_relay = [
    wordmark(RELAY, "Relay"),
    eyebrow(RELAY, "Version 2.0 is available today", pt=20),
    headline(RELAY, "<p>Built for teams that move fast.</p>", size="28px"),
    image(RELAY, unsplash("photo-1531297484001-80022131f5a1", 1200), pt=8, pb=4),
    section_label(RELAY, "WHAT'S NEW IN 2.0"),
    image_text(RELAY,
               unsplash("photo-1484480974693-6ca0a78fb36b", 480) + "&h=320",
               "Every thread distilled to three bullets, ready before your standup. "
               "No more scrolling back through a hundred messages to find what was decided.",
               heading="Smart Recaps", position="right", img_width="190px"),
    image_text(RELAY,
               unsplash("photo-1454165804606-c3d57bc86b40", 480) + "&h=320",
               "Capture the why behind every call, not just the what. "
               "Search it weeks or months later — it's all there, in context.",
               heading="Decision Log", position="left", img_width="190px"),
    image_text(RELAY,
               unsplash("photo-1506784983877-45594efa4cbe", 480) + "&h=320",
               "Auto-block your calendar during digest time. "
               "Relay keeps interruptions out so your team can actually do the work.",
               heading="Focus Hours", position="right", img_width="190px"),
    stats(RELAY, [("4,200+", "Teams on Relay"), ("31%", "Fewer meetings"),
                  ("99.99%", "Uptime")], bg=RELAY.surface),
    body(RELAY, "<p>Rolling out to every workspace this week — no upgrade needed on Team "
                "and Business plans.</p>", align="center", bg=RELAY.surface, pt=20, pb=4),
    button(RELAY, "Explore Relay 2.0 →", bg=RELAY.surface),
    social(RELAY, bg=RELAY.surface),
    footer(RELAY, "You're receiving this because you have a Relay workspace. "
                  "Manage your email preferences or unsubscribe anytime.", bg=RELAY.surface),
]


# ── Template: Newsletter — "The Quill" (editorial publication) ────────────────
# Quill is Builder's editorial brand: warm off-white, deep maroon, Georgia.
# Newsletter format: nameplate → hero story → two article previews with side
# images → centered reader quote → CTA. Uses hero, section_label, image_text,
# and quote blocks — the widest spread of any template so far.

QUILL = Theme(font="Georgia", ink="#1a1210", body="#5a4e47", accent="#8B2020",
              accent_soft="#f9f4f2", surface="#f7f2ed", border="#e5ddd6")

newsletter_quill = [
    wordmark(QUILL, "The Quill", bg=QUILL.surface),
    headline(QUILL, "<p>What great designers do differently</p>",
             bg=QUILL.surface, size="26px", pt=32, pb=8),
    lead(QUILL, "<p>The habits that separate craft from coincidence.</p>",
         bg=QUILL.surface, pt=4, pb=40),
    body(QUILL, "<p>Welcome back. This month we went deep on craft — what it actually "
                "takes to make something feel inevitable. Two stories worth your morning.</p>",
         pt=24, pb=12),
    divider(QUILL, pt=20, pb=4),
    section_label(QUILL, "This month's highlights", pt=16),
    image_text(QUILL,
               unsplash("photo-1455390582262-044cdead277a", 480) + "&h=320",
               "Designers who ship things people love almost always describe the same "
               "turning point: the moment they stopped fighting the limits and started "
               "designing inside them.",
               heading="On constraints and the brief",
               position="right", img_width="180px", pt=16, pb=16),
    divider(QUILL, pt=24, pb=4),
    image_text(QUILL,
               unsplash("photo-1481627834876-b7833e8f5570", 480) + "&h=320",
               "The designers we spoke to disagree with the 'nobody reads' headline. "
               "The ones who read widely — not just design books — make connections "
               "that specialists miss. It shows in the work.",
               heading="The case for reading outside your field",
               position="left", img_width="180px", pt=16, pb=16),
    quote(QUILL,
          "The Quill is the only newsletter I open the morning it arrives. "
          "It treats design as a practice, not a toolset.",
          "Ananya Krishnan", "Senior Product Designer, Cartograph",
          bg=QUILL.surface),
    body(QUILL, "<p>There's a lot more in this issue — interviews, links worth saving, "
                "and one tool we've been quietly recommending to everyone we know.</p>",
         align="center", bg=QUILL.surface, pt=8, pb=4),
    button(QUILL, "Read all stories →", bg=QUILL.surface, pt=16, pb=40),
    social(QUILL, bg=QUILL.surface),
    footer(QUILL, "You're receiving The Quill because you subscribed at thequill.co. "
                  "Unsubscribe anytime.", bg=QUILL.surface),
]


# ── Template: Product Launch — "Fronds" (earthy botanical boutique) ───────────
# Fronds is Builder's earthy boutique brand. Warm greens, Georgia, generous
# whitespace. This template announces a fresh spring batch of flowering plants.
# Uses: logo wordmark, product_card, stats, and the full warm-green palette.

FRONDS = Theme(font="Georgia", ink="#1c2b1c", body="#4a5c4a", accent="#3A6B35",
               accent_soft="#eef4ea", surface="#f2f7ef", border="#cddbc6")
FRONDS.band = "#e4eed9"

fronds_launch = [
    wordmark(FRONDS, "Fronds", bg=FRONDS.surface),
    headline(FRONDS, "<p>The new batch is here.</p>", bg=FRONDS.surface, size="34px",
             pt=28, pb=10),
    lead(FRONDS, "<p>Twenty-three new varieties, all rooted and ready to go home.</p>",
         bg=FRONDS.surface, pt=4, pb=20),
    image(FRONDS, unsplash("photo-1526397751294-331021109fbd", 1200), pt=0, pb=0, pl=0, pr=0, radius="0"),
    divider(FRONDS, pt=20, pb=4),
    body(FRONDS, "<p>Every spring we do a single run of new arrivals — plants we've been "
                 "growing since the previous autumn, chosen for variety and vigour. "
                 "This year's batch is the most diverse we've put together: trailing vines, "
                 "statement bloomers, and a handful of rarities we couldn't resist. "
                 "Everything is rooted, potted, and ready to leave.</p>",
         pt=28, pb=28),
    section_label(FRONDS, "Featured arrival", pt=16),
    product(FRONDS,
            unsplash("photo-1416879595882-3373a0480b5b", 900) + "&h=600",
            "Monstera Thai Constellation",
            "A slow-growing statement plant with creamy white variegation "
            "that makes every leaf unique. Potted in 14cm terracotta.",
            "£68"),
    image_text(FRONDS,
               unsplash("photo-1463936575829-25148e1db1b8", 480) + "&h=360",
               "Fast-growing, low-maintenance, and genuinely striking. "
               "The Pothos family is where we tell most beginners to start — "
               "they forgive missed waterings and thrive in almost any light.",
               heading="Pothos Golden & Marble Queen",
               position="left", img_width="180px"),
    stats(FRONDS, [("23", "New varieties"), ("4 years", "Grown in-house"),
                   ("30-day", "Settle-in guarantee")], bg=FRONDS.surface),
    body(FRONDS, "<p>All plants are ready to collect in-store or ship Monday–Thursday. "
                 "Each comes with a care card and our 30-day settle-in guarantee — "
                 "if it doesn't thrive in the first month, we'll replace it.</p>",
         bg=FRONDS.surface, pt=28, pb=8),
    button(FRONDS, "Browse the spring batch →", bg=FRONDS.surface),
    social(FRONDS, bg=FRONDS.surface),
    footer(FRONDS, "You're receiving this because you signed up in-store or online at "
                   "fronds.co. Unsubscribe anytime.", bg=FRONDS.surface),
]


TEMPLATES = {
    "Welcome & Onboarding": welcome_relay,
    "Promotional Offer": promo_wovenly,
    "Product Release": release_relay,
    "Newsletter": newsletter_quill,
    "Product Launch": fronds_launch,
}


def main():
    write_fixtures = "--fixtures" in sys.argv
    out_dir = os.path.join(os.path.dirname(__file__), "..", "letters", "public", "_tpl_preview")
    os.makedirs(out_dir, exist_ok=True)

    fixture_entries = []
    for sort, (name, blocks) in enumerate(TEMPLATES.items(), start=1):
        html = EmailCompiler(blocks, preview_text=name).compile()
        slug = name.lower().replace(" & ", "-").replace(" ", "-")
        with open(os.path.join(out_dir, f"{slug}.html"), "w") as f:
            f.write(html)
        print(f"wrote {slug}.html  ({len(blocks)} blocks)")
        fixture_entries.append({
            "doctype": "Letters Template",
            "name": name,
            "title": name,
            "sort_order": sort,
            "is_active": 1,
            "blocks_json": json.dumps(blocks),
        })

    if write_fixtures:
        fixture_path = os.path.join(
            os.path.dirname(__file__), "..", "letters", "letters", "fixtures", "letters_template.json")
        with open(fixture_path, "w") as f:
            json.dump(fixture_entries, f, indent=2, ensure_ascii=False)
        print(f"wrote fixtures ({len(fixture_entries)} templates)")


if __name__ == "__main__":
    main()
