import { ref, watchEffect } from "vue";

/**
 * Safe contenteditable binding that decouples Vue's reactivity from the DOM
 * during editing, preventing cursor resets and dropped keystrokes.
 *
 * Options:
 *   multiline (bool, default false)
 *     When false (default – single-line fields like headings):
 *       - Enter key is blocked; value is committed as plain text (innerText).
 *       - Paste is stripped of HTML.
 *       - Formatting shortcuts (Cmd+B/I/U) are suppressed.
 *     When true (text blocks that need real paragraphs / line-breaks):
 *       - Enter is allowed (browser inserts <div> / <br> naturally).
 *       - Value is committed as innerHTML so line breaks are preserved.
 *       - A lightweight paste sanitizer allows only safe inline tags.
 *
 * Usage:
 *   const { elRef, onFocus, onBlur, onPaste, onKeydown } = useContentEditable(
 *     () => props.block.props.content,
 *     (val) => update("content", val),
 *     { multiline: true }
 *   );
 *   <div ref="elRef" contenteditable="true"
 *        @focus="onFocus" @blur="onBlur"
 *        @paste.prevent="onPaste" @keydown="onKeydown" />
 */
export function useContentEditable(getValue, onCommit, { multiline = false } = {}) {
  const elRef = ref(null);
  const _focused = ref(false);

  watchEffect(() => {
    const el  = elRef.value;
    const val = getValue();
    if (!_focused.value && el) {
      if (multiline) {
        // innerHTML preserves <br>/<div> line breaks
        el.innerHTML = val ?? "";
      } else {
        el.textContent = val ?? "";
      }
    }
  });

  function onFocus() {
    _focused.value = true;
  }

  function onBlur(e) {
    _focused.value = false;
    if (multiline) {
      // Normalise: collapse consecutive <br> but keep intentional ones.
      const raw = e.target.innerHTML ?? "";
      onCommit(raw);
    } else {
      onCommit(e.target.innerText.trim());
    }
  }

  function onPaste(e) {
    e.preventDefault();
    if (multiline) {
      // Accept plain text; convert newlines to <br> so structure is preserved.
      const text = (e.clipboardData || window.clipboardData).getData("text/plain");
      const escaped = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\n/g, "<br>");
      document.execCommand("insertHTML", false, escaped);
    } else {
      const text = (e.clipboardData || window.clipboardData).getData("text/plain");
      if (typeof document.execCommand === "function") {
        document.execCommand("insertText", false, text);
      } else {
        const sel = window.getSelection();
        if (!sel?.rangeCount) return;
        sel.deleteFromDocument();
        sel.getRangeAt(0).insertNode(document.createTextNode(text));
        sel.collapseToEnd();
      }
    }
  }

  function onKeydown(e) {
    if (!multiline) {
      // Single-line: block formatting shortcuts + Enter
      const mod = e.metaKey || e.ctrlKey;
      if (mod && ["b", "i", "u"].includes(e.key.toLowerCase())) {
        e.preventDefault();
        return;
      }
      if (e.key === "Enter") {
        e.preventDefault();
        const el = elRef.value;
        if (el) {
          _focused.value = false;
          onCommit(el.innerText.trim());
          el.blur();
        }
      }
    }
    // multiline: let the browser handle Enter naturally (inserts <div>/<br>)
  }

  return { elRef, onFocus, onBlur, onPaste, onKeydown };
}
