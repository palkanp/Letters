import { ref, provide } from "vue";
import { BLOCK_SCHEMA } from "../blockSchema";

// The left-sidebar block picker: which blocks can be added, where a new block
// lands (top-level / inside a container / inside a column), the hover preview
// card, and the drag-to-canvas drop. Owns all picker state so BuilderPage only
// wires it to the template. Provides `openPicker` for nested blocks to call.
export function useBlockPicker(editorStore) {
  // pickerTarget: null = closed
  //   { mode: 'top', afterIndex: N }                  — add to top-level canvas
  //   { mode: 'child', parentId: X, afterIndex: N }   — add inside a container
  const pickerTarget = ref(null);

  function openPicker(target) {
    if (typeof target === "number") {
      // legacy: called with just an afterIndex number (from BlockAdderRow)
      pickerTarget.value = { mode: "top", afterIndex: target };
    } else {
      // called from container with { parentId, afterIndex }
      pickerTarget.value = { mode: "child", ...target };
    }
  }
  provide("openPicker", openPicker);

  const availableBlocks = [
    { type: "text",          label: "Text",         icon: "type" },
    { type: "image",         label: "Image",        icon: "image" },
    { type: "header",        label: "Header",       icon: "award" },
    { type: "hero",          label: "Hero",         icon: "layout" },
    { type: "image_text",    label: "Image + Text", icon: "sidebar" },
    { type: "button",        label: "Button",       icon: "square" },
    { type: "columns",       label: "Columns",      icon: "columns" },
    { type: "link_list",     label: "Link List",    icon: "list" },
    { type: "quote",         label: "Quote",        icon: "message-square" },
    { type: "social",        label: "Social",       icon: "share-2" },
    { type: "product_card",  label: "Product",      icon: "shopping-bag" },
    { type: "video_thumb",   label: "Video",        icon: "play-circle" },
    { type: "spacer",        label: "Spacer",       icon: "minus" },
    { type: "section_label", label: "Section Label", icon: "tag" },
    { type: "divider",       label: "Divider",      icon: "more-horizontal" },
    { type: "footer",        label: "Footer",       icon: "align-justify" },
  ];

  // Smart "Add block": if a container is selected, add inside it; else append.
  function onAddBlock() {
    const sel = editorStore.selectedBlock;
    if (sel?.type === "container") {
      openPicker({ mode: "child", parentId: sel.id, afterIndex: (sel.children?.length ?? 1) - 1 });
    } else {
      openPicker({ mode: "top", afterIndex: editorStore.blocks.length - 1 });
    }
  }

  // Smart "Add container": if a container is selected, nest inside it; else append.
  function addContainer() {
    const sel = editorStore.selectedBlock;
    if (sel?.type === "container") {
      editorStore.addChildBlock(sel.id, "container", (sel.children?.length ?? 1) - 1);
    } else {
      editorStore.addBlock("container", editorStore.blocks.length - 1);
    }
  }

  function closePicker() {
    pickerTarget.value = null;
    hideBlockPreview();
  }

  function insertBlock(type) {
    if (!pickerTarget.value) {
      editorStore.addBlock(type, editorStore.blocks.length - 1);
    } else if (pickerTarget.value.mode === "column") {
      editorStore.addBlockToColumn(
        pickerTarget.value.blockId,
        pickerTarget.value.colIndex,
        type,
        pickerTarget.value.afterIndex,
      );
    } else if (pickerTarget.value.mode === "child") {
      editorStore.addChildBlock(pickerTarget.value.parentId, type, pickerTarget.value.afterIndex);
    } else {
      editorStore.addBlock(type, pickerTarget.value.afterIndex);
    }
    closePicker();
    scrollToSelected();
  }

  function scrollToSelected() {
    const id = editorStore.selectedBlockId;
    if (!id) return;
    setTimeout(() => {
      const el = document.querySelector(`[data-block-id="${id}"]`);
      el?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 50);
  }

  // ── Block hover preview ─────────────────────────────────────────────────────
  const blockPreview = ref({ type: null, label: null, block: null, style: {} });
  let _previewTimer = null;

  function showBlockPreview(type, e) {
    clearTimeout(_previewTimer);
    const schema = BLOCK_SCHEMA[type] ?? {};
    const defaults = schema.defaults ?? {};
    const previewBlock = { id: 0, type, props: JSON.parse(JSON.stringify(defaults)) };
    if (type === "columns") {
      previewBlock.props.column_count = "3";
      previewBlock.props.padding_top = 16;
      previewBlock.props.padding_bottom = 16;
      previewBlock.props.padding_left = 16;
      previewBlock.props.padding_right = 16;
      previewBlock.props.col_gap = 16;
      const dummyCopy = [
        "<strong>Design</strong><br>Build beautiful emails with a drag-and-drop editor.",
        "<strong>Personalise</strong><br>Add dynamic fields to tailor every message.",
        "<strong>Send</strong><br>Deliver to your list with one click.",
      ];
      previewBlock.columns = dummyCopy.map((html, i) => ({
        blocks: [{
          id: i + 1,
          type: "text",
          props: {
            html_content: `<p style="font-size:12px;color:#374151;line-height:1.5;margin:0;font-family:sans-serif">${html}</p>`,
            background_color: "#ffffff",
            padding_top: 12, padding_right: 10, padding_bottom: 12, padding_left: 10,
          },
        }],
      }));
    }
    if (type === "social") {
      previewBlock.props.x_url = "https://x.com";
      previewBlock.props.linkedin_url = "https://linkedin.com";
      previewBlock.props.github_url = "https://github.com";
    }
    if (type === "spacer") {
      previewBlock.props.background_color = "#f3f4f6";
      previewBlock.props.height = 80;
    }
    // Position to the right of the sidebar
    const rect = e.currentTarget.closest("aside").getBoundingClientRect();
    const top = Math.min(e.currentTarget.getBoundingClientRect().top, window.innerHeight - 320);
    blockPreview.value = {
      type,
      label: schema.label ?? type,
      block: previewBlock,
      style: { left: rect.right + 8 + "px", top: top + "px" },
    };
  }

  function hideBlockPreview() {
    clearTimeout(_previewTimer);
    _previewTimer = setTimeout(() => { blockPreview.value = { type: null, label: null, block: null, style: {} }; }, 80);
  }

  // ── Drag-to-canvas drop (still supported — appends at end) ───────────────────
  let dragging = null;
  function onCanvasDrop() {
    if (dragging) {
      editorStore.addBlock(dragging.type);
      dragging = null;
    }
  }

  return {
    pickerTarget, openPicker, availableBlocks,
    onAddBlock, addContainer, closePicker, insertBlock,
    blockPreview, showBlockPreview, hideBlockPreview, onCanvasDrop,
  };
}
