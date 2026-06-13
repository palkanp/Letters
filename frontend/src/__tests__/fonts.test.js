/**
 * Tests for fonts.js — web font helpers and regression guards.
 *
 * Covers:
 *  1. fontStack() resolves system and web fonts correctly
 *  2. isWebFont() correctly identifies web fonts vs system fonts
 *  3. googleFontsUrl() generates correct Google Fonts URLs
 *  4. WEB_FONT_META weights are sane (only real weights, no gaps that cause faking)
 *  5. FONT_STACKS contains all web font names with correct fallback stacks
 *  6. blockSchema weight options are the 4 standard values
 */

import { describe, it, expect } from "vitest";
import {
  FONT_STACKS,
  WEB_FONT_META,
  FONT_OPTIONS,
  fontStack,
  isWebFont,
  googleFontsUrl,
} from "../fonts";
import { readFileSync } from "fs";
import { resolve } from "path";

// ---------------------------------------------------------------------------
// 1. fontStack()
// ---------------------------------------------------------------------------

describe("fontStack()", () => {
  it("resolves a system font", () => {
    expect(fontStack("Arial")).toBe("Arial, Helvetica, sans-serif");
  });

  it("resolves a web font with quoted name and fallback", () => {
    const stack = fontStack("Inter");
    expect(stack).toContain("'Inter'");
    expect(stack).toContain("Arial");
  });

  it("returns fallback for unknown font name", () => {
    expect(fontStack("Unknown Font", "my-fallback")).toBe("my-fallback");
  });

  it("returns empty fallback when name is empty", () => {
    expect(fontStack("", "fallback")).toBe("fallback");
    expect(fontStack(null, "fallback")).toBe("fallback");
  });
});

// ---------------------------------------------------------------------------
// 2. isWebFont()
// ---------------------------------------------------------------------------

describe("isWebFont()", () => {
  it("returns true for all WEB_FONT_META entries", () => {
    for (const name of Object.keys(WEB_FONT_META)) {
      expect(isWebFont(name), `${name} should be a web font`).toBe(true);
    }
  });

  it("returns false for system fonts", () => {
    for (const name of ["Arial", "Georgia", "Verdana", "Courier New"]) {
      expect(isWebFont(name), `${name} should NOT be a web font`).toBe(false);
    }
  });

  it("returns false for empty / unknown input", () => {
    expect(isWebFont("")).toBe(false);
    expect(isWebFont(null)).toBe(false);
    expect(isWebFont("Comic Sans")).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// 3. googleFontsUrl()
// ---------------------------------------------------------------------------

describe("googleFontsUrl()", () => {
  it("returns null for empty input", () => {
    expect(googleFontsUrl([])).toBeNull();
    expect(googleFontsUrl(null)).toBeNull();
  });

  it("returns null when only system fonts are passed", () => {
    expect(googleFontsUrl(["Arial", "Georgia"])).toBeNull();
  });

  it("returns a valid Google Fonts URL for a single web font", () => {
    const url = googleFontsUrl(["Inter"]);
    expect(url).toContain("fonts.googleapis.com");
    expect(url).toContain("family=Inter");
    expect(url).toContain("wght@");
    expect(url).toContain("display=swap");
  });

  it("includes all declared weights for the font", () => {
    const url = googleFontsUrl(["Inter"]);
    const weights = WEB_FONT_META["Inter"].weights;
    for (const w of weights) {
      expect(url).toContain(String(w));
    }
  });

  it("handles multiple web fonts in one URL", () => {
    const url = googleFontsUrl(["Inter", "Poppins"]);
    expect(url).toContain("family=Inter");
    expect(url).toContain("family=Poppins");
  });

  it("deduplicates repeated font names", () => {
    const url = googleFontsUrl(["Inter", "Inter", "Inter"]);
    const count = (url.match(/family=Inter/g) || []).length;
    expect(count).toBe(1);
  });

  it("ignores system fonts mixed in with web fonts", () => {
    const url = googleFontsUrl(["Arial", "Inter", "Georgia"]);
    expect(url).not.toContain("Arial");
    expect(url).not.toContain("Georgia");
    expect(url).toContain("Inter");
  });
});

// ---------------------------------------------------------------------------
// 4. WEB_FONT_META weight sanity
// ---------------------------------------------------------------------------

describe("WEB_FONT_META weight declarations", () => {
  const VALID_WEIGHTS = new Set([100, 200, 300, 400, 500, 600, 700, 800, 900]);

  for (const [name, meta] of Object.entries(WEB_FONT_META)) {
    it(`${name}: all declared weights are valid CSS values`, () => {
      for (const w of meta.weights) {
        expect(VALID_WEIGHTS.has(w), `Weight ${w} is not a valid CSS font-weight`).toBe(true);
      }
    });

    it(`${name}: includes 400 (regular) and 700 (bold)`, () => {
      expect(meta.weights).toContain(400);
      expect(meta.weights).toContain(700);
    });

    it(`${name}: googleFamily is a non-empty string`, () => {
      expect(typeof meta.googleFamily).toBe("string");
      expect(meta.googleFamily.length).toBeGreaterThan(0);
    });

    it(`${name}: fallback is a non-empty CSS font stack`, () => {
      expect(typeof meta.fallback).toBe("string");
      expect(meta.fallback.length).toBeGreaterThan(0);
    });
  }
});

// ---------------------------------------------------------------------------
// 5. FONT_STACKS completeness
// ---------------------------------------------------------------------------

describe("FONT_STACKS completeness", () => {
  it("contains all web font names", () => {
    for (const name of Object.keys(WEB_FONT_META)) {
      expect(FONT_STACKS).toHaveProperty(name);
    }
  });

  it("web font stacks quote the font name", () => {
    for (const name of Object.keys(WEB_FONT_META)) {
      expect(FONT_STACKS[name]).toContain(`'${name}'`);
    }
  });

  it("web font stacks include a system fallback", () => {
    for (const name of Object.keys(WEB_FONT_META)) {
      const stack = FONT_STACKS[name];
      // Must have at least one comma-separated fallback after the web font
      const parts = stack.split(",");
      expect(parts.length).toBeGreaterThan(1);
    }
  });

  it("contains all system fonts", () => {
    for (const name of ["Arial", "Helvetica", "Georgia", "Verdana", "Courier New"]) {
      expect(FONT_STACKS).toHaveProperty(name);
    }
  });
});

// ---------------------------------------------------------------------------
// 6. FONT_OPTIONS — all web fonts are listed
// ---------------------------------------------------------------------------

describe("FONT_OPTIONS", () => {
  it("lists all web fonts", () => {
    const optionValues = FONT_OPTIONS.map((o) => o.value);
    for (const name of Object.keys(WEB_FONT_META)) {
      expect(optionValues, `${name} missing from FONT_OPTIONS`).toContain(name);
    }
  });

  it("lists all system fonts", () => {
    const optionValues = FONT_OPTIONS.map((o) => o.value);
    for (const name of Object.keys(FONT_STACKS).filter((n) => !isWebFont(n))) {
      expect(optionValues, `System font ${name} missing from FONT_OPTIONS`).toContain(name);
    }
  });
});

// ---------------------------------------------------------------------------
// 7. blockSchema weight options
// ---------------------------------------------------------------------------

describe("blockSchema font weight options", () => {
  const SRC = readFileSync(resolve(__dirname, "../blockSchema.js"), "utf-8");

  it("includes Normal (400)", () => {
    expect(SRC).toContain('"400"');
  });

  it("includes Medium (500)", () => {
    expect(SRC).toContain('"500"');
  });

  it("includes Semibold (600)", () => {
    expect(SRC).toContain('"600"');
  });

  it("includes Bold (700)", () => {
    expect(SRC).toContain('"700"');
  });
});
