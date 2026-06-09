import { ref, watchEffect } from "vue";

/**
 * Safe contenteditable binding that decouples Vue's reactivity from the DOM
 * during editing, preventing cursor resets and dropped keystrokes.
 *
 * Also enforces plain-text-only editing:
 *   - Paste is intercepted and the clipboard's plain-text value is inserted
 *     via execCommand so the cursor position is preserved.
 *   - Common formatting shortcuts (Cmd/Ctrl + B/I/U) are suppressed so the
 *     user can never inject HTML tags that our onBlur → innerText would strip.
 *   - Enter key is blocked (email builder controls line breaks via block
 *     structure, not inline newlines inside a single editable field).
 *
 * Usage:
 *   const { elRef, onFocus, onBlur, onPaste, onKeydown } = useContentEditable(
 *     () => props.block.props.content,
 *     (val) => update("content", val)
 *   );
 *
 *   <div ref="elRef" contenteditable="true"
 *        @focus="onFocus" @blur="onBlur"
 *        @paste.prevent="onPaste" @keydown="onKeydown" />
 *
 * How it works:
 *   - The DOM is only updated from props when the element is NOT focused.
 *   - While the user types, Vue's reactive re-renders do NOT touch the element.
 *   - On blur, the value is committed back to the store once via innerText,
 *     which is safe because no HTML can ever be inserted.
 *   - watchEffect re-runs when elRef.value changes (v-if/v-else remounts)
 *     so initial content is always set correctly.
 */
export function useContentEditable(getValue, onCommit) {
  const elRef = ref(null);
  const _focused = ref(false);

  watchEffect(() => {
    const el = elRef.value;
    // Access getValue() so watchEffect tracks it as a dependency.
    const val = getValue();
    if (!_focused.value && el) {
      // Only sync from store to DOM when not editing.
      el.textContent = val ?? "";
    }
  });

  function onFocus() {
    _focused.value = true;
  }

  function onBlur(e) {
    _focused.value = false;
    // innerText is safe here: because onPaste and onKeydown below prevent any
    // HTML from ever entering the element, innerText === the user's plain text.
    onCommit(e.target.innerText.trim());
  }

  /**
   * Strip HTML from pasted content — always insert as plain text at the
   * current cursor position so copy-paste from rich editors (Google Docs,
   * Word, web pages) never injects tags.
   */
  function onPaste(e) {
    e.preventDefault();
    const text = (e.clipboardData || window.clipboardData).getData("text/plain");
    // execCommand keeps cursor position; fallback for environments where it
    // isn't supported (rare) is a no-op rather than a corrupt insert.
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

  /**
   * Block keyboard shortcuts that would insert formatting HTML:
   *   Cmd/Ctrl + B  → <b> / <strong>
   *   Cmd/Ctrl + I  → <em>
   *   Cmd/Ctrl + U  → <u>
   * Also block Enter so that multi-line content can't be created inside a
   * single field (the block system handles vertical structure).
   */
  function onKeydown(e) {
    const mod = e.metaKey || e.ctrlKey;
    if (mod && ["b", "i", "u"].includes(e.key.toLowerCase())) {
      e.preventDefault();
      return;
    }
    if (e.key === "Enter") {
      e.preventDefault();
      // Commit on Enter for keyboard-friendly UX (blur equivalent)
      const el = elRef.value;
      if (el) {
        _focused.value = false;
        onCommit(el.innerText.trim());
        el.blur();
      }
    }
  }

  return { elRef, onFocus, onBlur, onPaste, onKeydown };
}
