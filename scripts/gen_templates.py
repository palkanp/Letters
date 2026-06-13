"""Generates letters/letters/fixtures/letters_template.json with rich, realistic
templates. Run:  python3 scripts/gen_templates.py
"""
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "letters", "letters", "fixtures", "letters_template.json")


def b(type_, **props):
    block = {"type": type_}
    if props:
        block["props"] = props
    return block


# ── 1. Monthly Newsletter — "Northwind Coffee Co." ──────────────────────────
newsletter = [
    b("header", tagline="THE NORTHWIND DISPATCH · ISSUE 14", tagline_color="#6b7280", border_bottom=True),
    b("hero",
      heading="Spring has landed in the roastery",
      subheading="New single-origins, a café that finally has a name, and the return of the cold brew everyone keeps emailing us about.",
      background_color="#f8f5f0", heading_color="#1c1917", subheading_color="#57534e",
      heading_size="32px", padding_top=48, padding_bottom=40),
    b("text",
      html_content="<p>Hi friend,</p><p>It's been a busy month at the roastery. We brought in three new harvests, opened the doors to our first permanent café, and roasted more coffee in March than in any month since we started in a garage four years ago. Here's everything worth knowing.</p>",
      font_size="16px", line_height="1.7", padding_top=32, padding_bottom=8),
    b("section_label", label="WHAT'S NEW THIS MONTH"),
    b("image_text",
      heading="Ethiopia Guji — back in stock",
      text="Bright, floral, and unmistakably jasmine. This year's Guji lot is the cleanest cup we've tasted in three seasons. Available as whole bean or ground, while the harvest lasts.",
      image_position="right"),
    b("image_text",
      heading="The café finally has a name: Northwind & Co.",
      text="After months of arguing over the whiteboard, we landed on something simple. Come visit us at 212 Harbour Street — we're open 7am to 4pm, seven days a week, with a pour-over bar and far too many pastries.",
      image_position="left"),
    b("image_text",
      heading="Cold brew is back",
      text="You asked, we listened. Our 18-hour cold brew returns this week in bottles and on tap at the café. It's smooth, low-acid, and dangerously easy to drink by the litre.",
      image_position="right"),
    b("divider", padding_top=24, padding_bottom=8),
    b("quote",
      quote="Northwind's Guji is the only coffee my partner and I agree on. That's a miracle in our house.",
      author="Maya Fernandes", role="Subscriber since 2022",
      background_color="#f8f5f0", border_color="#d6cfc4"),
    b("section_label", label="FROM THE ROASTERY"),
    b("text",
      html_content="<p>A quick thank-you. Every bag you buy goes a little further than the coffee — this quarter we've paid <strong>23% above the Fair Trade floor</strong> directly to the farms we work with. That only happens because you keep choosing us over the supermarket shelf. It matters. Thank you.</p>",
      font_size="15px", line_height="1.7", padding_top=8),
    b("button", label="Shop this month's coffee →", url="#", color="#1c1917", text_color="#ffffff", button_padding="normal", padding_top=8),
    b("divider", padding_top=24, padding_bottom=4),
    b("social", x_url="https://x.com", instagram_url="https://instagram.com", website_url="https://example.com", color="#57534e", align="center"),
    b("footer", text="You're receiving the Northwind Dispatch because you bought coffee from us or signed up at the café. Unsubscribe anytime — no hard feelings.", background_color="#f8f5f0", text_color="#78716c"),
]

# ── 2. Product Announcement — "Driftwave" (SaaS) ────────────────────────────
announcement = [
    b("header", tagline="PRODUCT ANNOUNCEMENT", tagline_color="#94a3b8", background_color="#0f172a", tagline_color_unused=None, border_bottom=False),
    b("hero",
      heading="Introducing Driftwave Boards",
      subheading="The fastest way to turn a messy backlog into a plan your whole team can actually follow.",
      background_color="#0f172a", heading_color="#f1f5f9", subheading_color="#94a3b8",
      heading_size="36px", padding_top=56, padding_bottom=48),
    b("text",
      html_content="<p>For two years the number one request from Driftwave customers has been the same: <strong>“give us a way to plan, not just track.”</strong> Today we're shipping exactly that.</p><p>Boards is a planning surface that lives right alongside your tasks. Drag work across stages, group by owner or sprint, and watch the timeline update itself. No exports, no second tool, no Monday-morning spreadsheet.</p>",
      font_size="16px", line_height="1.7", padding_top=36, padding_bottom=8),
    b("section_label", label="WHAT YOU CAN DO NOW"),
    b("image_text",
      heading="Plan visually, in seconds",
      text="Drag cards between stages and the dates, dependencies, and owner workloads recalculate instantly. What used to take a planning meeting now takes a coffee break.",
      image_position="left"),
    b("image_text",
      heading="See who's actually overloaded",
      text="Group any board by teammate and Driftwave shows you, in plain colour, who has room this week and who's drowning. Rebalance before things slip, not after.",
      image_position="right"),
    b("image_text",
      heading="One source of truth",
      text="Boards read from the same tasks your team already updates. Change something on a board and it's reflected everywhere — no syncing, no stale copies, no “which version is right?”",
      image_position="left"),
    b("button", label="See Boards in action →", url="#", color="#2563eb", text_color="#ffffff", button_padding="normal", padding_top=32, padding_bottom=8),
    b("divider", padding_top=24),
    b("quote",
      quote="We cancelled two other tools the week Boards shipped. It does the planning and the tracking, and our standups are ten minutes shorter.",
      author="Priya Nair", role="Head of Engineering, Cartograph",
      background_color="#f8fafc", border_color="#cbd5e1"),
    b("text",
      html_content="<p>Boards is rolling out to every workspace this week — no upgrade needed on Team and Business plans. Open Driftwave and look for the new <strong>Boards</strong> tab in your sidebar.</p>",
      font_size="15px", line_height="1.7", align="center", padding_top=16),
    b("divider", padding_top=8, padding_bottom=4),
    b("social", x_url="https://x.com", linkedin_url="https://linkedin.com", youtube_url="https://youtube.com", color="#64748b", align="center"),
    b("footer", text="You're getting this because you have a Driftwave account. Manage your email preferences in Settings → Notifications.", background_color="#f8fafc", text_color="#64748b"),
]

# ── 3. Welcome Email — "Lumen" (habit app) ──────────────────────────────────
welcome = [
    b("header", tagline="WELCOME TO LUMEN", tagline_color="#166534", border_bottom=True),
    b("hero",
      heading="You're in. Let's build something.",
      subheading="Lumen works best when you start small. Here's how to set up your first habit in the next five minutes.",
      background_color="#f0fdf4", heading_color="#14532d", subheading_color="#166534",
      heading_size="30px", padding_top=48, padding_bottom=40),
    b("text",
      html_content="<p>Hi there,</p><p>Welcome aboard — we're genuinely glad you're here. Lumen isn't about tracking forty things at once. It's about doing one or two things consistently until they stick. Let's get your first one going.</p>",
      font_size="16px", line_height="1.7", padding_top=32, padding_bottom=8),
    b("section_label", label="GET STARTED IN 3 STEPS"),
    b("image_text",
      heading="1 · Pick one habit, not ten",
      text="Open the app and choose a single thing you want to do daily — a ten-minute walk, two pages of a book, a glass of water when you wake up. Smaller than feels impressive. That's the point.",
      image_position="left"),
    b("image_text",
      heading="2 · Set a time and a cue",
      text="Tell Lumen when it should nudge you, and tie it to something you already do (“after I make coffee”). Habits stick to other habits far better than they stick to willpower.",
      image_position="right"),
    b("image_text",
      heading="3 · Check in tonight",
      text="That's it. Do the thing, tap the circle, watch the streak start. Miss a day? Lumen never breaks your streak for one slip — because real life happens and guilt isn't a feature.",
      image_position="left"),
    b("button", label="Set up my first habit", url="#", color="#16a34a", text_color="#ffffff", button_padding="normal", padding_top=24),
    b("divider", padding_top=16),
    b("quote",
      quote="I've started and quit five habit apps. Lumen is the first one I've kept past a month — because it doesn't shame me when I slip.",
      author="Daniel Osei", role="Lumen member, 211-day streak",
      background_color="#f0fdf4", border_color="#bbf7d0"),
    b("text",
      html_content="<p>One last thing: if you ever get stuck, just reply to this email. A real person on our team reads every message — usually within a day. Need a hand right now? Visit our <a href=\"#\">Help Centre</a>.</p>",
      font_size="14px", line_height="1.7", align="center", text_color="#4b5563", padding_top=16),
    b("footer", text="You're receiving this because you created a Lumen account. If this wasn't you, just ignore it and the account won't activate.", background_color="#f0fdf4", text_color="#4d7c5f"),
]

# ── 4. Promotional Offer — "Atlas Apparel" ──────────────────────────────────
promo = [
    b("header", tagline="ATLAS APPAREL", tagline_color="#9a3412", border_bottom=True),
    b("hero",
      heading="40% off everything. 72 hours only.",
      subheading="Our biggest sale of the season ends Sunday at midnight. Use code SPRING40 at checkout — no minimum, no exclusions.",
      background_color="#fff7ed", heading_color="#9a3412", subheading_color="#c2410c",
      heading_size="34px", padding_top=52, padding_bottom=40),
    b("button", label="Shop the sale →", url="#", color="#ea580c", text_color="#ffffff", button_padding="normal", padding_top=8, padding_bottom=8),
    b("text",
      html_content="<p>This is the one we tell you to wait for. Everything — new arrivals included — is 40% off for the next three days. Here's where we'd start.</p>",
      font_size="15px", line_height="1.7", align="center", text_color="#78716c", padding_top=8, padding_bottom=8),
    b("divider", padding_top=16),
    b("section_label", label="WORTH GRABBING"),
    b("product_card",
      title="The Everyday Merino Crew",
      description="Soft, temperature-regulating merino that works under a jacket or on its own. The one customers buy in three colours.",
      price="$54 (was $90)", button_label="Shop now", button_url="#",
      button_color="#ea580c", title_color="#1c1917"),
    b("product_card",
      title="Atlas Field Trousers",
      description="Water-resistant, built to move, and somehow still smart enough for the office. Our best-reviewed item two years running.",
      price="$78 (was $130)", button_label="Shop now", button_url="#",
      button_color="#ea580c", title_color="#1c1917"),
    b("product_card",
      title="The Weekender Tote",
      description="Waxed canvas, leather handles, and enough room for a two-night trip. It ages beautifully and outlasts everything you'll pack in it.",
      price="$96 (was $160)", button_label="Shop now", button_url="#",
      button_color="#ea580c", title_color="#1c1917"),
    b("divider", padding_top=16),
    b("quote",
      quote="I waited for this sale all year and bought three things in one go. The merino crew alone is worth full price.",
      author="Sophie Lindqvist", role="Verified buyer",
      background_color="#fff7ed", border_color="#fed7aa"),
    b("button", label="Take 40% off everything", url="#", color="#ea580c", text_color="#ffffff", button_padding="normal", padding_top=24, padding_bottom=8),
    b("text",
      html_content="<p>Sale ends Sunday at 11:59pm. Code SPRING40 applies automatically at checkout. Discount can't be combined with other offers or applied to gift cards.</p>",
      font_size="12px", line_height="1.6", align="center", text_color="#a8a29e", padding_top=8, padding_bottom=8),
    b("social", instagram_url="https://instagram.com", x_url="https://x.com", website_url="https://example.com", color="#9a3412", align="center"),
    b("footer", text="You're receiving this because you've shopped with Atlas Apparel. Prefer fewer emails? Update your preferences anytime.", background_color="#fff7ed", text_color="#b45309"),
]

# ── 5. Weekly Digest — "The Frontier" ───────────────────────────────────────
digest = [
    b("header", tagline="THE FRONTIER · WEEKLY", tagline_color="#a5b4fc", background_color="#1e1b4b", border_bottom=False),
    b("hero",
      heading="This week in brief",
      subheading="The five things worth knowing from the past seven days — read it in under four minutes.",
      background_color="#1e1b4b", heading_color="#e0e7ff", subheading_color="#a5b4fc",
      heading_size="30px", padding_top=44, padding_bottom=36),
    b("text",
      html_content="<p>Good morning. It was a heavy news week, so we cut hard. Here's the signal, none of the noise. Let's go.</p>",
      font_size="16px", line_height="1.7", padding_top=28, padding_bottom=8),
    b("section_label", label="TOP STORIES"),
    b("text",
      html_content="<p><strong>1 · The funding winter is thawing — selectively.</strong></p><p>Early-stage rounds ticked up 18% this quarter, but the money is pooling around a handful of AI infrastructure names. Founders outside that lane are still finding the room cold. <a href=\"#\">Read the full breakdown →</a></p>",
      padding_top=8, padding_bottom=4),
    b("divider", padding_top=4, padding_bottom=4, border_color="#e0e7ff"),
    b("text",
      html_content="<p><strong>2 · A 28-year-old's side project is now critical internet plumbing.</strong></p><p>An open-source library maintained by one person quietly ended up inside half the apps you use. This week's outage was a reminder of how fragile that arrangement is. <a href=\"#\">Why it matters →</a></p>",
      padding_top=4, padding_bottom=4),
    b("divider", padding_top=4, padding_bottom=4, border_color="#e0e7ff"),
    b("text",
      html_content="<p><strong>3 · Remote work isn't dead — it just moved cities.</strong></p><p>New census data shows the people who left big metros in 2021 mostly stayed gone. Mid-size cities are the quiet winners, and their rents now show it. <a href=\"#\">See the maps →</a></p>",
      padding_top=4, padding_bottom=16),
    b("section_label", label="ALSO WORTH YOUR TIME"),
    b("link_list",
      heading="",
      items=[
        {"title": "The best long-read of the week", "url": "#", "description": "A reported piece on how one town rebuilt its high street from scratch."},
        {"title": "A tool we started using", "url": "#", "description": "It turns meeting notes into action items without the creepy always-listening part."},
        {"title": "The chart that explains everything", "url": "#", "description": "One graph on energy prices that reframes the whole debate."},
      ],
      style="numbered", link_color="#4f46e5"),
    b("section_label", label="FROM THE EDITOR"),
    b("text",
      html_content="<p>A small ask: if a friend would like The Frontier, forward this to them. We don't run ads and we don't sell your data — word of mouth is the entire growth strategy, and it's worked for 40,000 readers so far.</p>",
      font_size="15px", line_height="1.7", padding_top=8),
    b("button", label="Forward to a friend", url="#", color="#4f46e5", text_color="#ffffff", button_padding="normal", padding_top=16),
    b("divider", padding_top=16, padding_bottom=4),
    b("social", x_url="https://x.com", linkedin_url="https://linkedin.com", website_url="https://example.com", color="#6366f1", align="center"),
    b("footer", text="You're subscribed to The Frontier Weekly. Unsubscribe in one click anytime — we'll never make it hard.", background_color="#eef2ff", text_color="#6366f1"),
]


def strip_unused(blocks):
    # remove any accidental None / placeholder props
    for blk in blocks:
        props = blk.get("props")
        if props:
            blk["props"] = {k: v for k, v in props.items() if v is not None and not k.endswith("_unused")}
    return blocks


def apply_font(blocks, font):
    """Force a single font family across every block in a template, so a template
    never mixes typefaces. Blocks that don't take a font (divider, spacer, social)
    are left untouched."""
    no_font = {"divider", "spacer", "social"}
    for blk in blocks:
        if blk["type"] in no_font:
            continue
        blk.setdefault("props", {})["font_family"] = font
    return blocks


def add_images(blocks, logo_text, keywords):
    """Seed templates with *relevant* placeholder imagery: a branded logo in the
    header, and topical photos (via LoremFlickr keyword search) in image+text
    rows / product cards — consuming the keyword list in order."""
    logo = f"https://placehold.co/180x48/efefef/9ca3af?text={logo_text}"
    kw = list(keywords)
    lock = 0
    for blk in blocks:
        t = blk["type"]
        props = blk.setdefault("props", {})
        if t == "header":
            props["logo_url"] = logo
        elif t in ("image_text", "product_card"):
            lock += 1
            terms = kw.pop(0) if kw else "abstract"
            w, h = (480, 360) if t == "image_text" else (600, 400)
            props["image_url"] = f"https://loremflickr.com/{w}/{h}/{terms}?lock={lock}"
            if t == "image_text":
                props.setdefault("image_width", "200px")
    return blocks


# Per-template single font + relevant placeholder imagery (keywords match each
# image+text / product block in order).
apply_font(newsletter, "Georgia")
add_images(newsletter, "Northwind", ["coffee,beans", "cafe,coffeeshop", "coldbrew,icedcoffee"])

apply_font(announcement, "Inter")
add_images(announcement, "Driftwave", ["kanban,software", "team,office", "laptop,dashboard"])

apply_font(welcome, "Poppins")
add_images(welcome, "Lumen", ["walking,outdoors", "reading,book", "morning,sunrise"])

apply_font(promo, "Arial")
add_images(promo, "Atlas", ["sweater,knitwear", "trousers,clothing", "tote,bag"])

apply_font(digest, "Georgia")
add_images(digest, "The+Frontier", [])


# DocType is autonamed `field:title`, so each fixture's `name` must equal its title.
_defs = [
    ("Monthly Newsletter", 1, newsletter),
    ("Product Announcement", 2, announcement),
    ("Welcome Email", 3, welcome),
    ("Promotional Offer", 4, promo),
    ("Weekly Digest", 5, digest),
]
fixtures = [
    {
        "doctype": "Letters Template",
        "name": title,
        "title": title,
        "sort_order": order,
        "is_active": 1,
        "blocks_json": json.dumps(strip_unused(blocks), ensure_ascii=False),
    }
    for title, order, blocks in _defs
]

with open(OUT, "w") as f:
    json.dump(fixtures, f, indent=2, ensure_ascii=False)
    f.write("\n")

print(f"Wrote {len(fixtures)} templates to {OUT}")
for fx in fixtures:
    print(f"  - {fx['title']}: {len(json.loads(fx['blocks_json']))} blocks")
