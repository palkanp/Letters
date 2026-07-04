/*
 * Rasterize the starter templates' brand logos, feature icons, and social-icon
 * masks from SVG to PNG.
 *
 * Why: Gmail, Outlook, Yahoo and AOL do not render SVG <img> sources — they show
 * a broken-image placeholder — so every SVG logo/icon in an email is invisible in
 * the inbox. Raster PNG is the only email-safe option (see scripts/gen_logos.py).
 *
 * This writes:
 *   letters/public/images/<brand>/<logo>.png        (from the committed .svg)
 *   letters/public/images/meridian/icon-*.png        (feature icons)
 *   letters/public/images/social-masks/<slug>.png    (alpha masks for social.py)
 *
 * The social masks are single-colour glyphs whose alpha channel is the coverage;
 * social.py tints them to the user-chosen colour at send time with Pillow (no
 * runtime SVG rasterizer needed). Glyph paths are read straight from social.py's
 * _SOCIAL_ICONS via a tiny AST dump, so that stays the single source of truth.
 *
 * Dev-time only — not a runtime dependency. Run from the repo root:
 *     npm i @resvg/resvg-js        # once, anywhere on PATH / node_modules
 *     node scripts/gen_email_assets.mjs
 */
import { Resvg } from "@resvg/resvg-js";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const IMG = path.join(ROOT, "letters", "public", "images");

function renderToPng(svg, fitTo) {
  const r = new Resvg(svg, { fitTo, font: { loadSystemFonts: true } });
  return r.render().asPng();
}

function svgToPng(srcRel, outRel, fitTo) {
  const svg = fs.readFileSync(path.join(IMG, srcRel), "utf8");
  const out = path.join(IMG, outRel);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, renderToPng(svg, fitTo));
  console.log("wrote", outRel);
}

// ── Brand logos (rendered at ~4x display height for retina crispness) ────────
// display heights: meridian/arc 32px, kiln/relay 28px.
const LOGOS = [
  ["meridian/logo.svg", "meridian/logo.png", 128],
  ["arc/logo.svg", "arc/logo.png", 128],
  ["kiln/logo.svg", "kiln/logo.png", 112],
  ["relay/logo-blue.svg", "relay/logo-blue.png", 112],
  ["relay/logo.svg", "relay/logo.png", 112],
];
for (const [src, out, h] of LOGOS) {
  svgToPng(src, out, { mode: "height", value: h });
}

// ── Meridian feature icons (52px display → 4x) ───────────────────────────────
for (const name of ["icon-video", "icon-docs", "icon-community"]) {
  svgToPng(`meridian/${name}.svg`, `meridian/${name}.png`, { mode: "width", value: 208 });
}

// ── Social-icon alpha masks, from social.py's _SOCIAL_ICONS ──────────────────
const dump = execFileSync(
  "python3.11",
  [
    "-c",
    [
      "import ast,json,sys",
      "t=ast.parse(open(sys.argv[1]).read())",
      "for n in ast.walk(t):",
      " tgts=n.targets if isinstance(n,ast.Assign) else [n.target] if isinstance(n,ast.AnnAssign) else []",
      " if any(getattr(x,'id',None)=='_SOCIAL_ICONS' for x in tgts):",
      "  d=ast.literal_eval(n.value); print(json.dumps({k:{'label':v[0],'path':v[1]} for k,v in d.items()}))",
    ].join("\n"),
    path.join(ROOT, "letters", "letters", "utils", "block_renderers", "social.py"),
  ],
  { encoding: "utf8" },
);
const icons = JSON.parse(dump.trim().split("\n").pop());
const slug = (label) => label.toLowerCase().replaceAll(" / ", "-").replaceAll(" ", "-");
for (const { label, path: d } of Object.values(icons)) {
  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">` +
    `<path fill="#000000" d="${d}"/></svg>`;
  const out = path.join(IMG, "social-masks", `${slug(label)}.png`);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, renderToPng(svg, { mode: "width", value: 128 }));
  console.log("wrote", `social-masks/${slug(label)}.png`);
}
