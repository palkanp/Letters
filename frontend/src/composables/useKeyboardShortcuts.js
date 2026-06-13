import { onMounted, onUnmounted } from "vue";

// True when focus is in a text field where editor shortcuts shouldn't hijack
// the key (so Cmd+C copies text, not the block).
function inTextField() {
  return document.activeElement?.isContentEditable ||
    ["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName);
}

// Wires the builder's global keyboard + trackpad shortcuts and the unsaved-
// changes guard. Takes the actions it drives so it stays decoupled from the
// page's other state.
export function useKeyboardShortcuts({ editorStore, saveNow, openPreview, stepZoom, canvasZoom }) {
  function beforeUnloadHandler(e) {
    if (editorStore.isDirty) {
      e.preventDefault();
      e.returnValue = ""; // required for Chrome
    }
  }

  function keydownHandler(e) {
    // Non-modifier shortcuts (only when not in a text field)
    if (!e.metaKey && !e.ctrlKey) {
      if (!inTextField()) {
        if (e.key === "Escape") {
          editorStore.selectBlock(null);
          return;
        }
        if ((e.key === "Delete" || e.key === "Backspace") && editorStore.selectedBlockId) {
          e.preventDefault();
          editorStore.removeBlock(editorStore.selectedBlockId);
          return;
        }
      }
      return;
    }
    // Undo: Cmd/Ctrl + Z (without Shift)
    if (e.key === "z" && !e.shiftKey) {
      if (inTextField()) return;
      e.preventDefault();
      editorStore.undo();
      return;
    }
    // Redo: Cmd/Ctrl + Shift + Z  or  Ctrl + Y
    if ((e.key === "z" && e.shiftKey) || (e.key === "y" && !e.shiftKey)) {
      if (inTextField()) return;
      e.preventDefault();
      editorStore.redo();
      return;
    }
    // Save: Cmd/Ctrl + S
    if (e.key === "s") {
      e.preventDefault();
      saveNow();
      return;
    }
    // Copy selected block: Cmd/Ctrl + C (only when not in a text field)
    if (e.key === "c") {
      if (inTextField()) return;
      if (editorStore.selectedBlockId) editorStore.copyBlock(editorStore.selectedBlockId);
      return;
    }
    // Paste block: Cmd/Ctrl + V (only when not in a text field)
    if (e.key === "v") {
      if (inTextField()) return;
      editorStore.pasteBlock();
      return;
    }
    // Duplicate selected block: Cmd/Ctrl + D
    if (e.key === "d") {
      if (inTextField()) return;
      e.preventDefault();
      if (editorStore.selectedBlockId) editorStore.duplicateBlock(editorStore.selectedBlockId);
      return;
    }
    // Preview: Cmd/Ctrl + Shift + P
    if (e.key === "p" && e.shiftKey) {
      e.preventDefault();
      openPreview();
      return;
    }
    // Zoom in: Cmd/Ctrl + =  or  +
    if (e.key === "=" || e.key === "+") {
      e.preventDefault();
      stepZoom(1);
      return;
    }
    // Zoom out: Cmd/Ctrl + -
    if (e.key === "-") {
      e.preventDefault();
      stepZoom(-1);
      return;
    }
    // Reset zoom: Cmd/Ctrl + 0
    if (e.key === "0") {
      e.preventDefault();
      canvasZoom.value = 1;
      return;
    }
  }

  function wheelHandler(e) {
    if (!e.ctrlKey) return;
    e.preventDefault();
    stepZoom(e.deltaY < 0 ? 1 : -1);
  }

  onMounted(() => {
    window.addEventListener("beforeunload", beforeUnloadHandler);
    window.addEventListener("keydown", keydownHandler);
    window.addEventListener("wheel", wheelHandler, { passive: false });
  });
  onUnmounted(() => {
    window.removeEventListener("beforeunload", beforeUnloadHandler);
    window.removeEventListener("keydown", keydownHandler);
    window.removeEventListener("wheel", wheelHandler);
  });
}
