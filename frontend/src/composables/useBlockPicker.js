import { ref, provide } from "vue";
import { BLOCK_SCHEMA } from "../blockSchema";
import { BLOCK_PRESET_DEFS } from "../blockPresets";

export function useBlockPicker(editorStore) {
  // pickerTarget: null  = no explicit placement
  //   { mode: 'top', afterIndex: N }                          — specific row adder
  //   { mode: 'child', parentId: X, afterIndex: N }           — inside container
  //   { mode: 'column', blockId: X, colIndex: N, afterIndex } — inside column
  const pickerTarget = ref(null);

  function openPicker(target) {
    if (typeof target === "number") {
      pickerTarget.value = { mode: "top", afterIndex: target };
    } else {
      pickerTarget.value = { mode: "child", ...target };
    }
  }
  provide("openPicker", openPicker);

  // Grouped block list. Items with a `section` key render as headers.
  const availableBlocks = [
    { section: "Basics" },
    { type: "text",          label: "Text",         icon: "type" },
    { type: "image",         label: "Image",        icon: "image" },
    { type: "button",        label: "Button",       icon: "square" },
    { type: "divider",       label: "Divider",      icon: "more-horizontal" },
    { type: "spacer",        label: "Spacer",       icon: "minus" },
    { type: "container",     label: "Container",    icon: "box" },
    { section: "Presets" },
    { type: "three_col",     label: "3 Columns",    icon: "columns" },
    { type: "text_cols",     label: "Text Columns", icon: "columns" },
    { type: "header",        label: "Logo",         icon: "award" },
    { type: "hero",          label: "Hero",         icon: "layout" },
    { type: "image_text",    label: "Image + Text", icon: "sidebar" },
    { type: "product_card",  label: "Product Card", icon: "shopping-bag" },
    { type: "quote",         label: "Quote",        icon: "message-square" },
    { type: "video_thumb",   label: "Video",        icon: "play-circle" },
    { type: "link_list",     label: "Link List",    icon: "list" },
    { type: "section_label", label: "Section Label", icon: "tag" },
    { type: "footer",        label: "Footer",       icon: "align-justify" },
    { section: "Other" },
    { type: "social",        label: "Social",       icon: "share-2" },
  ];

  function onAddBlock() {
    const sel = editorStore.selectedBlock;
    if (sel?.type === "container") {
      openPicker({ mode: "child", parentId: sel.id, afterIndex: (sel.children?.length ?? 1) - 1 });
      return;
    }
    if (sel) {
      const parent = _findParentContainer(sel.id);
      if (parent) {
        const idx = parent.children.findIndex((c) => c.id === sel.id);
        openPicker({ mode: "child", parentId: parent.id, afterIndex: idx });
        return;
      }
    }
    openPicker({ mode: "top", afterIndex: editorStore.blocks.length - 1 });
  }

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

  // Walk the block tree to find the nearest container parent of a given block id.
  function _findParentContainer(id, list = editorStore.blocks) {
    for (const b of list) {
      if (b.children?.some((c) => c.id === id)) return b.type === "container" ? b : null;
      if (b.children?.length) {
        const found = _findParentContainer(id, b.children);
        if (found !== undefined) return found;
      }
    }
    return undefined;
  }

  // Resolve where to insert: explicit pickerTarget wins; otherwise auto from selection.
  function _resolveTarget() {
    if (pickerTarget.value) return pickerTarget.value;
    const sel = editorStore.selectedBlock;
    if (sel?.type === "container") {
      return { mode: "child", parentId: sel.id, afterIndex: (sel.children?.length ?? 1) - 1 };
    }
    // If selected block is a child of a container, insert as sibling after it.
    if (sel) {
      const parent = _findParentContainer(sel.id);
      if (parent) {
        const idx = parent.children.findIndex((c) => c.id === sel.id);
        return { mode: "child", parentId: parent.id, afterIndex: idx };
      }
    }
    return { mode: "top", afterIndex: editorStore.blocks.length - 1 };
  }

  function insertBlock(type) {
    const target     = _resolveTarget();
    const presetDef  = BLOCK_PRESET_DEFS[type];
    const hadTarget  = !!pickerTarget.value;

    if (presetDef) {
      let options;
      if (target.mode === "column") {
        options = { mode: "column", parentId: target.blockId, colIndex: target.colIndex, afterIndex: target.afterIndex };
      } else if (target.mode === "child") {
        options = { mode: "child", parentId: target.parentId, afterIndex: target.afterIndex };
      } else {
        options = { mode: "top", afterIndex: target.afterIndex };
      }
      editorStore.insertBuiltBlock(presetDef, options);
    } else {
      if (target.mode === "column") {
        editorStore.addBlockToColumn(target.blockId, target.colIndex, type, target.afterIndex);
      } else if (target.mode === "child") {
        editorStore.addChildBlock(target.parentId, type, target.afterIndex);
      } else {
        editorStore.addBlock(type, target.afterIndex);
      }
    }

    // Only close the picker if it was explicitly opened via a row/container button.
    if (hadTarget) closePicker();
    else hideBlockPreview();
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
    const presetDef = BLOCK_PRESET_DEFS[type];

    let previewBlock;
    let label;

    if (presetDef) {
      // Build a lightweight preview from the preset definition
      let _pid = 0;
      function buildPreview(def) {
        const b = { id: _pid++, type: def.type, props: { ...def.props } };
        if (def.children?.length) b.children = def.children.map(buildPreview);
        return b;
      }
      previewBlock = buildPreview(presetDef);
      label = presetDef.label ?? type;
    } else {
      const schema = BLOCK_SCHEMA[type] ?? {};
      label = schema.label ?? type;
      const defaults = schema.defaults ?? {};
      previewBlock = { id: 0, type, props: JSON.parse(JSON.stringify(defaults)) };

      if (type === "text") {
        previewBlock.props.html_content = "<p>Sample text block. Edit content, font, size, and colour from the Inspector.</p>";
      }
      if (type === "image") {
        previewBlock.props.image_url = "";
      }
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
        previewBlock.props.color = "#9ca3af";
        previewBlock.props.icon_size = 20;
      }
      if (type === "spacer") {
        previewBlock.props.background_color = "#f3f4f6";
        previewBlock.props.height = 80;
      }
    }

    const rect = e.currentTarget.closest("aside").getBoundingClientRect();
    const top  = Math.min(e.currentTarget.getBoundingClientRect().top, window.innerHeight - 320);
    blockPreview.value = { type, label, block: previewBlock, style: { left: rect.right + 8 + "px", top: top + "px" } };
  }

  function hideBlockPreview() {
    clearTimeout(_previewTimer);
    _previewTimer = setTimeout(() => {
      blockPreview.value = { type: null, label: null, block: null, style: {} };
    }, 80);
  }

  let dragging = null;
  function onCanvasDrop() {
    if (dragging) { editorStore.addBlock(dragging.type); dragging = null; }
  }

  return {
    pickerTarget, openPicker, availableBlocks,
    onAddBlock, addContainer, closePicker, insertBlock,
    blockPreview, showBlockPreview, hideBlockPreview, onCanvasDrop,
  };
}
