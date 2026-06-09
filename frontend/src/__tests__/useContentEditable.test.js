/**
 * Tests for useContentEditable.js
 *
 * Covers:
 *  - DOM is populated from getValue() on mount
 *  - DOM is NOT updated while focused (_focused guard)
 *  - DOM IS updated after blur (unfocused again)
 *  - onBlur commits the current innerText value
 *  - onPaste strips HTML and inserts plain text
 *  - onKeydown blocks Cmd+B, Ctrl+B, Cmd+I, Cmd+U
 *  - onKeydown blocks Enter and triggers commit+blur
 *  - onKeydown allows normal characters through
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ref, nextTick } from "vue";
import { useContentEditable } from "../composables/useContentEditable";

// happy-dom provides a full DOM; we create a real <div> and wire it up manually.
function createEl() {
  const el = document.createElement("div");
  el.setAttribute("contenteditable", "true");
  document.body.appendChild(el);
  return el;
}

function setupComposable(initialValue = "hello") {
  const value   = ref(initialValue);
  const commits = [];
  const onCommit = (v) => { commits.push(v); value.value = v; };

  const { elRef, onFocus, onBlur, onPaste, onKeydown } = useContentEditable(
    () => value.value,
    onCommit
  );

  const el = createEl();
  elRef.value = el;          // simulate Vue wiring ref to the DOM element

  return { el, elRef, onFocus, onBlur, onPaste, onKeydown, value, commits };
}

beforeEach(() => {
  document.body.innerHTML = "";
  // happy-dom doesn't implement execCommand — stub it so onPaste tests work
  document.execCommand = vi.fn();
});

// ── Initialisation ────────────────────────────────────────────────────────────

it("populates the DOM element from getValue() via watchEffect", async () => {
  const { el } = setupComposable("initial text");
  await nextTick();
  expect(el.textContent).toBe("initial text");
});

it("re-syncs DOM when the reactive value changes while NOT focused", async () => {
  const { el, value } = setupComposable("first");
  await nextTick();
  value.value = "updated";
  await nextTick();
  expect(el.textContent).toBe("updated");
});

// ── Focus guard ───────────────────────────────────────────────────────────────

it("does NOT overwrite DOM while the element is focused", async () => {
  const { el, onFocus, value } = setupComposable("original");
  await nextTick();
  onFocus();                // user clicks in
  el.textContent = "user is typing…";
  value.value = "store update";  // unrelated store mutation
  await nextTick();
  // Element must still show what the user typed
  expect(el.textContent).toBe("user is typing…");
});

it("re-syncs DOM after blur if the store changed while focused", async () => {
  const { el, onFocus, onBlur, value } = setupComposable("original");
  await nextTick();
  onFocus();
  el.textContent = "typed";
  value.value = "store update";
  await nextTick();
  // Blur commits "typed" and clears _focused
  const blurEvent = { target: { innerText: "typed" } };
  onBlur(blurEvent);
  // Now re-sync to "store update" (which onBlur set via commit → value.value = "typed",
  // but let's update value to simulate an independent change)
  value.value = "from store";
  await nextTick();
  expect(el.textContent).toBe("from store");
});

// ── Blur / commit ─────────────────────────────────────────────────────────────

it("commits innerText on blur (trimmed)", () => {
  const { onFocus, onBlur, commits } = setupComposable("old");
  onFocus();
  onBlur({ target: { innerText: "  new value  " } });
  expect(commits).toEqual(["new value"]);
});

it("commit trims surrounding whitespace", () => {
  const { onFocus, onBlur, commits } = setupComposable("");
  onFocus();
  onBlur({ target: { innerText: "\n  trimmed\n" } });
  expect(commits[0]).toBe("trimmed");
});

// ── onPaste ───────────────────────────────────────────────────────────────────

it("onPaste calls preventDefault", () => {
  const { onPaste } = setupComposable();
  const event = {
    preventDefault: vi.fn(),
    clipboardData: { getData: vi.fn().mockReturnValue("plain text") },
  };
  onPaste(event);
  expect(event.preventDefault).toHaveBeenCalled();
});

it("onPaste reads text/plain from clipboardData", () => {
  const { onPaste } = setupComposable();
  const getData = vi.fn().mockReturnValue("pasted plain");
  const event = {
    preventDefault: vi.fn(),
    clipboardData: { getData },
  };
  onPaste(event);
  expect(getData).toHaveBeenCalledWith("text/plain");
});

// ── onKeydown — formatting shortcuts ──────────────────────────────────────────

describe("onKeydown — formatting shortcuts are blocked", () => {
  const FORMATTING_KEYS = [
    { key: "b", label: "Cmd+B" },
    { key: "i", label: "Cmd+I" },
    { key: "u", label: "Cmd+U" },
    { key: "B", label: "Cmd+Shift+B" },
  ];

  for (const { key, label } of FORMATTING_KEYS) {
    it(`blocks ${label} (metaKey)`, () => {
      const { onKeydown } = setupComposable();
      const event = { key, metaKey: true, ctrlKey: false, preventDefault: vi.fn() };
      onKeydown(event);
      expect(event.preventDefault).toHaveBeenCalled();
    });

    it(`blocks ${label} (ctrlKey)`, () => {
      const { onKeydown } = setupComposable();
      const event = { key, metaKey: false, ctrlKey: true, preventDefault: vi.fn() };
      onKeydown(event);
      expect(event.preventDefault).toHaveBeenCalled();
    });
  }
});

it("allows normal character keys through", () => {
  const { onKeydown } = setupComposable();
  const event = { key: "a", metaKey: false, ctrlKey: false, preventDefault: vi.fn() };
  onKeydown(event);
  expect(event.preventDefault).not.toHaveBeenCalled();
});

it("does NOT block Cmd+A (select all)", () => {
  const { onKeydown } = setupComposable();
  const event = { key: "a", metaKey: true, ctrlKey: false, preventDefault: vi.fn() };
  onKeydown(event);
  expect(event.preventDefault).not.toHaveBeenCalled();
});

// ── onKeydown — Enter ─────────────────────────────────────────────────────────

it("Enter calls preventDefault", async () => {
  const { onFocus, onKeydown, el } = setupComposable("text");
  await nextTick();
  onFocus();
  el.textContent = "some text";

  const blurSpy = vi.spyOn(el, "blur").mockImplementation(() => {});
  const event = { key: "Enter", metaKey: false, ctrlKey: false, preventDefault: vi.fn() };
  onKeydown(event);
  expect(event.preventDefault).toHaveBeenCalled();
});

it("Enter commits the current innerText", async () => {
  const { onFocus, onKeydown, el, commits } = setupComposable("original");
  await nextTick();
  onFocus();
  el.textContent = "committed via enter";
  el.innerText   = "committed via enter"; // happy-dom sync

  vi.spyOn(el, "blur").mockImplementation(() => {});
  const event = { key: "Enter", metaKey: false, ctrlKey: false, preventDefault: vi.fn() };
  onKeydown(event);
  expect(commits[0]).toBe("committed via enter");
});
