// Font definitions — single source of truth for the frontend.
// Mirrors letters/letters/utils/fonts.py exactly; keep the two in sync.
//
// Two categories:
//   • System fonts  — email-safe, no <link> needed, only 400/700 available.
//   • Web fonts     — loaded from Google Fonts, support 400/500/600/700.
//                     Email clients that don't support web fonts (Outlook on
//                     Windows) silently fall back to the system fallback stack.
//
// Blocks store the human font name (e.g. "Inter"). The full CSS stack and any
// required <link> tags are resolved at render time by the helpers below.

// ---------------------------------------------------------------------------
// System fonts (email-safe, 400 + 700 only)
// ---------------------------------------------------------------------------

const SYSTEM_FONT_STACKS = {
  // Sans-serif
  "Arial":           "Arial, Helvetica, sans-serif",
  "Helvetica":       "Helvetica, Arial, sans-serif",
  "Verdana":         "Verdana, Geneva, sans-serif",
  "Tahoma":          "Tahoma, Geneva, sans-serif",
  "Trebuchet MS":    "'Trebuchet MS', Helvetica, sans-serif",
  // Serif
  "Georgia":         "Georgia, 'Times New Roman', serif",
  "Times New Roman": "'Times New Roman', Times, serif",
  // Monospace
  "Courier New":     "'Courier New', Courier, monospace",
};

// ---------------------------------------------------------------------------
// Web fonts (Google Fonts, 400/500/600/700)
// ---------------------------------------------------------------------------
// weights lists the variants we request — only include weights the typeface
// actually ships (requesting a missing weight wastes a network round-trip and
// causes the browser to fake-bold/fake-oblique).
//
// Email client support:
//   ✅ Apple Mail (macOS / iOS), Gmail (web / Android / iOS), Outlook (Mac),
//      Samsung Mail, Yahoo Mail, Fastmail
//   ❌ Outlook on Windows (2016–365) — falls back to the system stack below

export const WEB_FONT_META = {
  "Inter":     { googleFamily: "Inter",     weights: [400, 500, 600, 700], fallback: "Arial, Helvetica, sans-serif" },
  "Roboto":    { googleFamily: "Roboto",    weights: [400, 500, 700],      fallback: "Arial, Helvetica, sans-serif" },
  "Open Sans": { googleFamily: "Open+Sans", weights: [400, 500, 600, 700], fallback: "Arial, Helvetica, sans-serif" },
  "Poppins":   { googleFamily: "Poppins",   weights: [400, 500, 600, 700], fallback: "Arial, Helvetica, sans-serif" },
};

// ---------------------------------------------------------------------------
// Combined stack map (used by fontStack())
// ---------------------------------------------------------------------------

export const FONT_STACKS = {
  ...SYSTEM_FONT_STACKS,
  ...Object.fromEntries(
    Object.entries(WEB_FONT_META).map(([name, { googleFamily, fallback }]) => [
      name,
      `'${name}', ${fallback}`,
    ])
  ),
};

// ---------------------------------------------------------------------------
// Ordered options for the Inspector's font <Select>
// ---------------------------------------------------------------------------

export const FONT_OPTIONS = [
  // Web fonts first — these support multiple weights
  { label: "Inter",            value: "Inter",            group: "Web fonts" },
  { label: "Roboto",           value: "Roboto",           group: "Web fonts" },
  { label: "Open Sans",        value: "Open Sans",        group: "Web fonts" },
  { label: "Poppins",          value: "Poppins",          group: "Web fonts" },
  // System fonts
  { label: "Arial",            value: "Arial",            group: "System fonts" },
  { label: "Helvetica",        value: "Helvetica",        group: "System fonts" },
  { label: "Verdana",          value: "Verdana",          group: "System fonts" },
  { label: "Tahoma",           value: "Tahoma",           group: "System fonts" },
  { label: "Trebuchet MS",     value: "Trebuchet MS",     group: "System fonts" },
  { label: "Georgia",          value: "Georgia",          group: "System fonts" },
  { label: "Times New Roman",  value: "Times New Roman",  group: "System fonts" },
  { label: "Courier New",      value: "Courier New",      group: "System fonts" },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Resolve a stored font name to its full CSS stack. */
export function fontStack(name, fallback = "") {
  return FONT_STACKS[(name || "").trim()] || fallback;
}

/** Return true if the font name is a web font (needs a Google Fonts <link>). */
export function isWebFont(name) {
  return Object.prototype.hasOwnProperty.call(WEB_FONT_META, (name || "").trim());
}

/**
 * Build a Google Fonts stylesheet URL for a set of font names.
 * Returns null when none of the names are web fonts.
 *
 * @param {string[]} names  - Array of font names (may include system fonts; they are ignored)
 * @returns {string|null}
 */
export function googleFontsUrl(names) {
  const families = [...new Set((names || []).map(n => (n || "").trim()))]
    .filter(n => WEB_FONT_META[n]);

  if (!families.length) return null;

  const params = families
    .map(name => {
      const { googleFamily, weights } = WEB_FONT_META[name];
      return `family=${googleFamily}:wght@${weights.join(";")}`;
    })
    .join("&");

  return `https://fonts.googleapis.com/css2?${params}&display=swap`;
}

/**
 * Inject Google Fonts <link> tags into document.head for the given font names.
 * Safe to call multiple times — skips fonts already injected.
 */
export function injectGoogleFonts(names) {
  const url = googleFontsUrl(names);
  if (!url) return;

  const id = "letters-google-fonts";
  const existing = document.getElementById(id);
  if (existing && existing.href === url) return;
  if (existing) existing.remove();

  const preconnect = document.createElement("link");
  preconnect.rel = "preconnect";
  preconnect.href = "https://fonts.googleapis.com";
  document.head.appendChild(preconnect);

  const preconnect2 = document.createElement("link");
  preconnect2.rel = "preconnect";
  preconnect2.href = "https://fonts.gstatic.com";
  preconnect2.crossOrigin = "anonymous";
  document.head.appendChild(preconnect2);

  const link = document.createElement("link");
  link.id = id;
  link.rel = "stylesheet";
  link.href = url;
  document.head.appendChild(link);
}
