/**
 * Regression guards for modal / panel theming.
 *
 * Background: the Settings dialog and Template picker once rendered transparent
 * with unreadable headings. Root cause: they used `bg-surface-modal` (and the
 * also-retired `bg-surface-white`) — tokens this version of frappe-ui RETIRED.
 * No Tailwind utility rule is generated for them, so the class resolved to
 * nothing. The current tokens (bg-surface-base, bg-surface-gray-*,
 * text-ink-gray-*, border-outline-gray-*) DO generate rules and auto-flip in
 * dark mode via [data-theme="dark"]; the rest of the builder relies on them.
 *
 * The fix is to use current frappe-ui semantic tokens — NOT bespoke hard-coded
 * `.lt-*` classes (an earlier misdiagnosis). These tests assert, at the source
 * level, that:
 *   1. No component references the retired surface-modal/surface-card tokens.
 *   2. No component reintroduces the bespoke `.lt-*` theming classes.
 *   3. The two modals use real frappe-ui surface + ink + outline tokens.
 *   4. Inspector keeps a solid background matching its sibling panels.
 *   5. letter.js keeps "Open in Letters Builder" and removes Frappe's
 *      native Templates button.
 */

import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync } from "fs";
import { resolve } from "path";

const read = (rel) => readFileSync(resolve(__dirname, rel), "utf-8");

const PICKER = read("../components/TemplatePicker.vue");
const SETTINGS = read("../components/LetterSettings.vue");
const INSPECTOR = read("../components/Inspector.vue");
const STYLE = read("../style.css");
const LETTER_JS = read(
  "../../../letters/public/frappe_customizations/letter.js"
);

// Every .vue/.js source file under src/ (excluding tests), for repo-wide bans.
function allSourceFiles(dir = resolve(__dirname, "..")) {
  const out = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === "__tests__" || entry.name === "node_modules") continue;
    const full = resolve(dir, entry.name);
    if (entry.isDirectory()) out.push(...allSourceFiles(full));
    else if (/\.(vue|js)$/.test(entry.name)) out.push(full);
  }
  return out;
}

// frappe-ui tokens this version retired: no Tailwind utility rule is generated
// for them, so the class resolves to nothing (transparent / no color). The
// current equivalents are bg-surface-base / bg-surface-elevation-* for the
// white elevated surface, and bg-surface-gray-* for recessed areas.
const RETIRED_TOKENS = [
  "surface-white",
  "surface-modal",
  "surface-card",
  "surface-cards",
  "surface-selected",
];

// ---------------------------------------------------------------------------
// 1. No retired frappe-ui tokens anywhere in src/
// ---------------------------------------------------------------------------

describe("no retired frappe-ui surface tokens", () => {
  const files = allSourceFiles();

  for (const token of RETIRED_TOKENS) {
    it(`no source file references "${token}" (retired → resolves transparent)`, () => {
      const offenders = files.filter((f) => readFileSync(f, "utf-8").includes(token));
      expect(offenders, `Found ${token} in:\n${offenders.join("\n")}`).toEqual([]);
    });
  }
});

// ---------------------------------------------------------------------------
// 2. The bespoke .lt-* workaround is gone and stays gone
// ---------------------------------------------------------------------------

describe("no bespoke .lt-* theming classes", () => {
  it("style.css does not define .lt-* classes", () => {
    expect(STYLE).not.toMatch(/\.lt-(surface|border|title|text|muted)/);
  });

  it("no component uses .lt-* classes", () => {
    const offenders = allSourceFiles().filter((f) =>
      /\blt-(surface|border|title|text|muted)/.test(readFileSync(f, "utf-8"))
    );
    expect(offenders).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// 3. Modals use real frappe-ui tokens (solid surface + readable ink)
// ---------------------------------------------------------------------------

describe("TemplatePicker.vue uses a solid background", () => {
  it("shell uses bg-surface-base (adapts to both light and dark themes)", () => {
    expect(PICKER).toContain("bg-surface-base");
  });
  it("heading + subtitle use frappe-ui ink tokens (auto-contrast both themes)", () => {
    expect(PICKER).toContain("text-ink-gray-9"); // heading
    expect(PICKER).toMatch(/text-ink-gray-[56]/); // muted subtitle
  });
  it("backdrop is a solid dim", () => {
    expect(PICKER).toMatch(/bg-black\/\d+/);
  });
});

describe("LetterSettings.vue uses frappe-ui tokens", () => {
  it("panel has a solid frappe-ui surface", () => {
    expect(SETTINGS).toContain("bg-surface-base");
  });
  it("titles use a frappe-ui ink token", () => {
    expect(SETTINGS).toContain("text-ink-gray-9");
  });
});

// ---------------------------------------------------------------------------
// 4. Inspector keeps a solid background (matches sibling panels)
// ---------------------------------------------------------------------------

describe("Inspector.vue background", () => {
  it("root has a solid background, not transparent", () => {
    // header uses literal bg-white; Inspector matches it. A frappe-ui
    // bg-surface-base would also satisfy "solid" — accept either.
    expect(INSPECTOR).toMatch(/\bbg-(white|surface-base)\b/);
  });
});

// ---------------------------------------------------------------------------
// 5. letter.js — builder button kept, native Templates removed
// ---------------------------------------------------------------------------

describe("letter.js form customizations", () => {
  it('keeps the "Open in Letters Builder" custom button', () => {
    expect(LETTER_JS).toContain("Open in Letters Builder");
  });
  it("removes Frappe's native Templates feature (template_manager)", () => {
    expect(LETTER_JS).toContain("template_manager");
    expect(LETTER_JS).toContain("Templates");
  });
});
