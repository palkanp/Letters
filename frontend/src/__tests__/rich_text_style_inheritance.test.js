/**
 * Tests for rich_text.vue style inheritance and bubble menu behaviour.
 *
 * Covers the recurring issues seen in audits:
 *  1. Block-level styles (font-size, font-weight, color, font-family,
 *     line-height, text-align, letter-spacing) must cascade through every
 *     ProseMirror child element — p, li, span, strong, b, em, i, h1-h6.
 *  2. `shouldShow` must not be set to `() => true` (bubble menu shows on
 *     selection only, not always).
 *  3. List markers must use `list-style-position: inside` so centered lists
 *     keep their markers in-line with the text.
 *  4. `.ProseMirror` inherits letter-spacing (not just font/color).
 */

import { readFileSync } from "fs";
import { resolve } from "path";
import { describe, it, expect } from "vitest";

const SRC = readFileSync(
  resolve(__dirname, "../components/blocks/rich_text.vue"),
  "utf-8"
);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Extract the <style> block text. */
function styleBlock() {
  const m = SRC.match(/<style[^>]*>([\s\S]*?)<\/style>/);
  return m ? m[1] : "";
}

/** Extract the <script setup> block text. */
function scriptBlock() {
  const m = SRC.match(/<script\b[^>]*>([\s\S]*?)<\/script>/);
  return m ? m[1] : "";
}

/** Extract the <template> block text. */
function templateBlock() {
  const m = SRC.match(/<template>([\s\S]*?)<\/template>/);
  return m ? m[1] : "";
}

// ---------------------------------------------------------------------------
// 1. CSS inheritance — every child element must inherit all block-level props
// ---------------------------------------------------------------------------

const STYLE_PROPS = [
  "font-size",
  "font-weight",
  "color",
  "line-height",
  "font-family",
  "text-align",
  "letter-spacing",
];

const INLINE_ELEMENTS = ["p", "li", "span", "strong", "b", "em", "i"];
const HEADING_ELEMENTS = ["h1", "h2", "h3", "h4", "h5", "h6"];

describe("rich_text CSS inheritance", () => {
  const css = styleBlock();

  for (const prop of STYLE_PROPS) {
    it(`${prop}: inherit !important appears for inline/block elements`, () => {
      // The rule must exist somewhere in the stylesheet for inline elements.
      // We check that the stylesheet contains a selector that targets at least
      // one of the inline elements with the expected declaration.
      const hasRule = INLINE_ELEMENTS.some((el) =>
        css.includes(`.ProseMirror ${el}`) || css.includes(`.ProseMirror p`)
      );
      expect(hasRule, `No ProseMirror child selector found in <style>`).toBe(true);

      // The declaration itself must appear.
      expect(
        css,
        `"${prop}: inherit !important" not found in <style>`
      ).toContain(`${prop}: inherit !important`);
    });
  }

  it("headings h1-h6 are included in inherit rules", () => {
    for (const h of HEADING_ELEMENTS) {
      expect(
        css,
        `Heading "${h}" missing from ProseMirror inherit rules`
      ).toContain(`.ProseMirror ${h}`);
    }
  });

  it("strong and b are included in inherit rules (block weight must override bold)", () => {
    expect(css).toContain(".ProseMirror strong");
    expect(css).toContain(".ProseMirror b");
  });
});

// ---------------------------------------------------------------------------
// 2. Bubble menu — must NOT use shouldShow: () => true
// ---------------------------------------------------------------------------

describe("bubble-menu behaviour", () => {
  const template = templateBlock();

  it("shouldShow: () => true is NOT set (bubble menu only on selection)", () => {
    expect(
      template,
      "Found `shouldShow: () => true` — bubble menu must only show on text selection, not always"
    ).not.toContain("shouldShow");
  });

  it("bubble-menu prop is present (menu is enabled)", () => {
    expect(template).toContain("bubble-menu");
  });
});

// ---------------------------------------------------------------------------
// 3. List markers — must use list-style-position: inside
// ---------------------------------------------------------------------------

describe("list style position", () => {
  const css = styleBlock();

  it("ul uses list-style-position: inside", () => {
    expect(css).toContain("list-style-position: inside");
  });

  it("ol uses list-style-position: inside", () => {
    // Both ul and ol blocks contain "list-style-position: inside"
    const matches = (css.match(/list-style-position:\s*inside/g) || []).length;
    expect(
      matches,
      "Expected list-style-position: inside for both ul and ol"
    ).toBeGreaterThanOrEqual(2);
  });
});

// ---------------------------------------------------------------------------
// 4. Prose max-width — must be overridden so content fills the full block
// ---------------------------------------------------------------------------

describe("prose max-width override", () => {
  const css = styleBlock();

  it(".rich-text-shell .prose has max-width: none", () => {
    expect(css).toContain(".rich-text-shell .prose");
    expect(css).toContain("max-width: none");
  });
});

// ---------------------------------------------------------------------------
// 5. Shell :style binding — all block-level props wired up
// ---------------------------------------------------------------------------

describe("rich-text-shell :style binding", () => {
  const template = templateBlock();

  const STYLE_BINDINGS = [
    "fontFamily",
    "fontSize",
    "fontWeight",
    "color",
    "lineHeight",
    "textAlign",
    "letterSpacing",
  ];

  for (const binding of STYLE_BINDINGS) {
    it(`shell :style includes ${binding}`, () => {
      expect(
        template,
        `"${binding}" missing from rich-text-shell :style binding`
      ).toContain(binding);
    });
  }
});
