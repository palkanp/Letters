import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { BLOCK_SCHEMA } from "../blockSchema";

export const useEditorStore = defineStore("editor", () => {
  const blocks         = ref([]);
  const renderedHtml   = ref("");
  const campaignName   = ref("");
  const campaignDoc    = ref(null);
  const emailWidth       = ref(600);
  const canvasBg         = ref("#ffffff");
  const selectedBlockId  = ref(null);
  const selectedBlockIds = ref(new Set()); // all selected block ids (for multi-select)
  const isDirty          = ref(false);
  const clipboard        = ref(null); // array of deep-cloned blocks, or null
  const styleClipboard   = ref(null); // copied style props object

  const SENT_STATUSES = ["Sent", "Sending", "Partial", "Failed"];
  const isReadOnly = computed(() => SENT_STATUSES.includes(campaignDoc.value?.status));

  const _idCounter = ref(0);
  function nextId() { return ++_idCounter.value; }

  function markDirty() { isDirty.value = true; }
  function clearDirty() { isDirty.value = false; }

  // ── Undo / Redo history ──────────────────────────────────────────────────────
  const _history = [];
  const _historyIndex = ref(-1);
  const MAX_HISTORY = 50;

  const canUndo = computed(() => _historyIndex.value > 0);
  const canRedo = computed(() => _historyIndex.value < _history.length - 1);

  let _historyDebounceTimer = null;

  function _pushHistory(immediate = false) {
    // Debounce rapid sequential calls (e.g. typing in an input) so they
    // produce a single undo entry. Structural operations pass immediate=true.
    if (!immediate) {
      clearTimeout(_historyDebounceTimer);
      _historyDebounceTimer = setTimeout(() => _commitHistory(), 600);
      return;
    }
    _commitHistory();
  }

  function _commitHistory() {
    clearTimeout(_historyDebounceTimer);
    // Drop any redo states beyond current position
    _history.splice(_historyIndex.value + 1);
    _history.push(JSON.parse(JSON.stringify(blocks.value)));
    if (_history.length > MAX_HISTORY) _history.shift();
    _historyIndex.value = _history.length - 1;
  }

  function undo() {
    if (!canUndo.value) return;
    _historyIndex.value--;
    blocks.value = JSON.parse(JSON.stringify(_history[_historyIndex.value]));
    markDirty();
  }

  function redo() {
    if (!canRedo.value) return;
    _historyIndex.value++;
    blocks.value = JSON.parse(JSON.stringify(_history[_historyIndex.value]));
    markDirty();
  }

  function _seedHistory() {
    _history.length = 0;
    _history.push(JSON.parse(JSON.stringify(blocks.value)));
    _historyIndex.value = 0;
  }

  // ── Recursive helpers ────────────────────────────────────────────────────────
  // Search top-level blocks, container children, AND column blocks.
  function findBlock(id, list = blocks.value) {
    for (const b of list) {
      if (b.id === id) return b;
      if (b.children?.length) {
        const found = findBlock(id, b.children);
        if (found) return found;
      }
      if (b.columns?.length) {
        for (const col of b.columns) {
          if (col.blocks?.length) {
            const found = findBlock(id, col.blocks);
            if (found) return found;
          }
        }
      }
    }
    return null;
  }

  const selectedBlock = computed(() => findBlock(selectedBlockId.value));

  // ── Top-level block operations ───────────────────────────────────────────────
  function addBlock(type, afterIndex = null) {
    _pushHistory(true);
    const newBlock = _createBlock(type, nextId());
    if (afterIndex === null || afterIndex === undefined) {
      blocks.value.push(newBlock);
    } else if (afterIndex < 0) {
      blocks.value.unshift(newBlock);
    } else {
      blocks.value.splice(afterIndex + 1, 0, newBlock);
    }
    selectedBlockId.value = newBlock.id;
    markDirty();
  }

  function removeBlock(id) {
    _pushHistory(true);
    function removeFrom(list) {
      const idx = list.findIndex((b) => b.id === id);
      if (idx !== -1) { list.splice(idx, 1); return true; }
      for (const b of list) {
        if (b.children && removeFrom(b.children)) return true;
        if (b.columns) {
          for (const col of b.columns) {
            if (col.blocks && removeFrom(col.blocks)) return true;
          }
        }
      }
      return false;
    }
    removeFrom(blocks.value);
    if (selectedBlockId.value === id) selectedBlockId.value = null;
    markDirty();
  }

  function moveBlock(fromIndex, toIndex) {
    _pushHistory(true);
    const item = blocks.value.splice(fromIndex, 1)[0];
    blocks.value.splice(toIndex, 0, item);
    markDirty();
  }

  function selectBlock(id) {
    if (isReadOnly.value) return;
    selectedBlockId.value = id;
    selectedBlockIds.value = id ? new Set([id]) : new Set();
  }

  function toggleInSelection(id) {
    if (isReadOnly.value) return;
    const next = new Set(selectedBlockIds.value);
    if (next.has(id)) {
      next.delete(id);
      if (selectedBlockId.value === id) {
        const remaining = [...next];
        selectedBlockId.value = remaining.length ? remaining[remaining.length - 1] : null;
      }
    } else {
      next.add(id);
      selectedBlockId.value = id;
    }
    selectedBlockIds.value = next;
  }

  function addRangeToSelection(ids) {
    if (isReadOnly.value) return;
    const next = new Set(selectedBlockIds.value);
    ids.forEach((id) => next.add(id));
    selectedBlockIds.value = next;
    if (ids.length) selectedBlockId.value = ids[ids.length - 1];
  }

  function updateBlockProps(id, props) {
    _pushHistory(); // debounced — rapid typing collapses into one undo entry
    const block = findBlock(id);
    if (block) { Object.assign(block.props, props); markDirty(); }
  }

  // Like updateBlockProps but does NOT push a history snapshot.
  // Use during continuous drags — call updateBlockProps once at drag START
  // to snapshot the pre-drag state, then call this on every move event.
  function updateBlockPropsLive(id, props) {
    const block = findBlock(id);
    if (block) { Object.assign(block.props, props); markDirty(); }
  }

  // ── Container child operations ───────────────────────────────────────────────
  function addChildBlock(parentId, type, afterIndex = null) {
    _pushHistory(true);
    const parent = findBlock(parentId);
    if (!parent) return;
    if (!parent.children) parent.children = [];
    const newBlock = _createBlock(type, nextId());
    if (afterIndex === null || afterIndex === undefined) {
      parent.children.push(newBlock);
    } else if (afterIndex < 0) {
      parent.children.unshift(newBlock);
    } else {
      parent.children.splice(afterIndex + 1, 0, newBlock);
    }
    selectedBlockId.value = newBlock.id;
    markDirty();
  }

  function moveChildBlock(parentId, fromIndex, toIndex) {
    _pushHistory(true);
    const parent = findBlock(parentId);
    if (!parent?.children) return;
    const item = parent.children.splice(fromIndex, 1)[0];
    parent.children.splice(toIndex, 0, item);
    markDirty();
  }

  // ── Columns child operations ─────────────────────────────────────────────────
  function addBlockToColumn(blockId, colIndex, type, afterIndex = null) {
    _pushHistory(true);
    const block = findBlock(blockId);
    if (!block?.columns) return;
    const col = block.columns[colIndex];
    if (!col) return;
    if (!col.blocks) col.blocks = [];
    const newBlock = _createBlock(type, nextId());
    if (afterIndex === null || afterIndex === undefined) {
      col.blocks.push(newBlock);
    } else if (afterIndex < 0) {
      col.blocks.unshift(newBlock);
    } else {
      col.blocks.splice(afterIndex + 1, 0, newBlock);
    }
    selectedBlockId.value = newBlock.id;
    markDirty();
  }

  function moveBlockInColumn(blockId, colIndex, fromIndex, toIndex) {
    _pushHistory(true);
    const block = findBlock(blockId);
    const col = block?.columns?.[colIndex];
    if (!col?.blocks) return;
    const item = col.blocks.splice(fromIndex, 1)[0];
    col.blocks.splice(toIndex, 0, item);
    markDirty();
  }

  function setColumnCount(blockId, count) {
    _pushHistory(true);
    const block = findBlock(blockId);
    if (!block?.columns) return;
    const current = block.columns.length;
    if (count > current) {
      for (let i = current; i < count; i++) {
        block.columns.push({ blocks: [] });
      }
    } else if (count < current) {
      block.columns.splice(count);
    }
    markDirty();
  }

  // ── Cross-level move (layers panel drag) ─────────────────────────────────────
  function moveBlockTo(blockId, targetParentId, targetIndex) {
    _pushHistory(true);
    if (targetParentId !== null && _isDescendant(blockId, targetParentId)) return;

    let moved = null;
    function detach(list) {
      const idx = list.findIndex((b) => b.id === blockId);
      if (idx !== -1) { moved = list.splice(idx, 1)[0]; return true; }
      for (const b of list) {
        if (b.children && detach(b.children)) return true;
        if (b.columns) {
          for (const col of b.columns) {
            if (col.blocks && detach(col.blocks)) return true;
          }
        }
      }
      return false;
    }
    detach(blocks.value);
    if (!moved) return;

    if (targetParentId === null) {
      const idx = Math.min(targetIndex, blocks.value.length);
      blocks.value.splice(idx, 0, moved);
    } else {
      const parent = findBlock(targetParentId);
      if (parent) {
        if (!parent.children) parent.children = [];
        const idx = Math.min(targetIndex, parent.children.length);
        parent.children.splice(idx, 0, moved);
      }
    }
    markDirty();
  }

  // Column-aware variant: detach blockId from wherever it is, then insert it
  // into columns[colIndex].blocks of the columnsParentId block at targetIndex.
  function moveBlockToColumn(blockId, columnsParentId, colIndex, targetIndex) {
    _pushHistory(true);

    let moved = null;
    function detach(list) {
      const idx = list.findIndex((b) => b.id === blockId);
      if (idx !== -1) { moved = list.splice(idx, 1)[0]; return true; }
      for (const b of list) {
        if (b.children && detach(b.children)) return true;
        if (b.columns) {
          for (const col of b.columns) {
            if (col.blocks && detach(col.blocks)) return true;
          }
        }
      }
      return false;
    }
    detach(blocks.value);
    if (!moved) return;

    const parent = findBlock(columnsParentId);
    if (!parent?.columns?.[colIndex]) { markDirty(); return; }
    const col = parent.columns[colIndex];
    const idx = Math.min(targetIndex, col.blocks.length);
    col.blocks.splice(idx, 0, moved);
    markDirty();
  }

  function _isDescendant(blockId, ofId) {
    const ancestor = findBlock(ofId);
    if (!ancestor) return false;
    function check(list) {
      for (const b of list) {
        if (b.id === blockId) return true;
        if (b.children && check(b.children)) return true;
        if (b.columns) {
          for (const col of b.columns) {
            if (col.blocks && check(col.blocks)) return true;
          }
        }
      }
      return false;
    }
    const sources = [];
    if (ancestor.children) sources.push(...ancestor.children);
    if (ancestor.columns) ancestor.columns.forEach(c => sources.push(...(c.blocks || [])));
    return check(sources);
  }

  function duplicateBlock(id) {
    _pushHistory(true);
    function cloneWithNewIds(b) {
      const clone = JSON.parse(JSON.stringify(b));
      clone.id = nextId();
      if (clone.children) clone.children = clone.children.map(cloneWithNewIds);
      if (clone.columns) {
        clone.columns = clone.columns.map(col => ({
          ...col,
          blocks: (col.blocks || []).map(cloneWithNewIds),
        }));
      }
      return clone;
    }

    const topIdx = blocks.value.findIndex((b) => b.id === id);
    if (topIdx !== -1) {
      const clone = cloneWithNewIds(blocks.value[topIdx]);
      blocks.value.splice(topIdx + 1, 0, clone);
      selectedBlockId.value = clone.id;
      markDirty();
      return;
    }

    function duplicateIn(list) {
      for (let i = 0; i < list.length; i++) {
        if (list[i].id === id) {
          const clone = cloneWithNewIds(list[i]);
          list.splice(i + 1, 0, clone);
          selectedBlockId.value = clone.id;
          markDirty();
          return true;
        }
        if (list[i].children && duplicateIn(list[i].children)) return true;
        if (list[i].columns) {
          for (const col of list[i].columns) {
            if (col.blocks && duplicateIn(col.blocks)) return true;
          }
        }
      }
      return false;
    }
    duplicateIn(blocks.value);
  }

  // Props that belong to content, not style — excluded from copyStyle / pasteStyle.
  const STYLE_EXCLUDED = new Set([
    "html_content", "heading", "subheading", "text", "image_url", "thumbnail_url",
    "video_url", "logo_url", "caption", "alt", "tagline", "logo_height",
    "url", "link_url", "button_url", "label", "title", "description", "price",
    "quote", "author", "role", "button_label", "items",
    "x_url", "linkedin_url", "instagram_url", "facebook_url",
    "youtube_url", "github_url", "website_url",
  ]);

  function copyStyle(id) {
    const block = findBlock(id);
    if (!block) return;
    const styleProps = {};
    for (const [k, v] of Object.entries(block.props)) {
      if (!STYLE_EXCLUDED.has(k)) styleProps[k] = v;
    }
    styleClipboard.value = styleProps;
  }

  function pasteStyle(id) {
    const block = findBlock(id);
    if (!block || !styleClipboard.value) return;
    const validKeys = new Set(Object.keys(BLOCK_SCHEMA[block.type]?.defaults ?? {}));
    const updates = {};
    for (const [k, v] of Object.entries(styleClipboard.value)) {
      if (validKeys.has(k) && !STYLE_EXCLUDED.has(k)) updates[k] = v;
    }
    if (Object.keys(updates).length) updateBlockProps(id, updates);
  }

  function copyBlock(id) {
    const block = findBlock(id);
    if (!block) return;
    clipboard.value = [JSON.parse(JSON.stringify(block))];
    try { localStorage.setItem("letters_clipboard", JSON.stringify(clipboard.value)); } catch {}
  }

  function copyBlocks(ids) {
    const list = ids.map((id) => findBlock(id)).filter(Boolean);
    if (!list.length) return;
    clipboard.value = list.map((b) => JSON.parse(JSON.stringify(b)));
    try { localStorage.setItem("letters_clipboard", JSON.stringify(clipboard.value)); } catch {}
  }

  function pasteBlock() {
    let data = clipboard.value;
    if (!data?.length) {
      try {
        const stored = localStorage.getItem("letters_clipboard");
        if (stored) data = JSON.parse(stored);
      } catch {}
    }
    if (!data?.length) return;
    _pushHistory(true);
    function cloneWithNewIds(b) {
      const clone = JSON.parse(JSON.stringify(b));
      clone.id = nextId();
      if (clone.children) clone.children = clone.children.map(cloneWithNewIds);
      if (clone.columns) {
        clone.columns = clone.columns.map(col => ({
          ...col,
          blocks: (col.blocks || []).map(cloneWithNewIds),
        }));
      }
      return clone;
    }
    const clones = data.map(cloneWithNewIds);
    const selIdx = blocks.value.findIndex((b) => b.id === selectedBlockId.value);
    if (selIdx !== -1) {
      blocks.value.splice(selIdx + 1, 0, ...clones);
    } else {
      blocks.value.push(...clones);
    }
    selectedBlockId.value = clones[clones.length - 1].id;
    selectedBlockIds.value = new Set(clones.map((c) => c.id));
    markDirty();
  }

  // Insert a pre-built block tree (from BLOCK_PRESET_DEFS) with fresh IDs.
  // mode: "top" | "child" | "column"
  function insertBuiltBlock(def, options = {}) {
    _pushHistory(true);
    const { mode = "top", afterIndex = null, parentId = null, colIndex = null } = options;

    function buildBlock(d) {
      const b = _createBlock(d.type, nextId());
      if (d.label) b.label = d.label;
      if (d.props) Object.assign(b.props, d.props);
      if (d.children?.length) b.children = d.children.map(buildBlock);
      return b;
    }
    const block = buildBlock(def);

    if (mode === "child" && parentId !== null) {
      const parent = findBlock(parentId);
      if (!parent) return;
      if (!parent.children) parent.children = [];
      const idx = afterIndex === null ? parent.children.length : afterIndex + 1;
      parent.children.splice(idx, 0, block);
    } else if (mode === "column" && parentId !== null && colIndex !== null) {
      const parent = findBlock(parentId);
      const col = parent?.columns?.[colIndex];
      if (!col) return;
      if (!col.blocks) col.blocks = [];
      const idx = afterIndex === null ? col.blocks.length : afterIndex + 1;
      col.blocks.splice(idx, 0, block);
    } else {
      if (afterIndex === null || afterIndex === undefined) {
        blocks.value.push(block);
      } else if (afterIndex < 0) {
        blocks.value.unshift(block);
      } else {
        blocks.value.splice(afterIndex + 1, 0, block);
      }
    }

    selectedBlockId.value = block.id;
    selectedBlockIds.value = new Set([block.id]);
    markDirty();
  }

  function setBlockLabel(id, label) {
    _pushHistory(true);
    const block = findBlock(id);
    if (!block) return;
    const trimmed = label?.trim();
    if (trimmed) block.label = trimmed;
    else delete block.label;
    markDirty();
  }

  // ── Persistence ──────────────────────────────────────────────────────────────
  function setRenderedHtml(html) {
    renderedHtml.value = html;
  }

  function _assignIds(list) {
    return (list || []).map((b) => {
      const result = { ...b, id: nextId() };

      // Container children
      if (b.children) {
        result.children = _assignIds(b.children);
      } else if (b.type === "container") {
        result.children = [];
      }

      // Columns nested blocks
      if (b.columns) {
        result.columns = b.columns.map(col => ({
          ...col,
          blocks: _assignIds(col.blocks || []),
        }));
      } else if (b.type === "columns") {
        const count = parseInt(b.props?.column_count || "2");
        result.columns = Array.from({ length: count }, () => ({ blocks: [] }));
      }

      return result;
    });
  }

  function _migrateBlock(b) {
    // Merge legacy "rich_text" type into "text"
    if (b.type === "rich_text") b = { ...b, type: "text" };
    // Migrate old plain-text "text" blocks: convert content → html_content
    if (b.type === "text" && b.props?.content !== undefined && !b.props?.html_content) {
      const escaped = b.props.content.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      b = { ...b, props: { ...b.props, html_content: `<p>${escaped}</p>` } };
      delete b.props.content;
    }
    if (b.children) b = { ...b, children: b.children.map(_migrateBlock) };
    if (b.columns) b = { ...b, columns: b.columns.map(col => ({ ...col, blocks: (col.blocks || []).map(_migrateBlock) })) };
    return b;
  }

  function loadFromDoc(doc) {
    campaignDoc.value  = doc;
    campaignName.value = doc.title;
    emailWidth.value   = doc.email_width || 600;
    canvasBg.value     = doc.canvas_background || "#ffffff";
    _idCounter.value   = 0;
    selectedBlockId.value = null;
    blocks.value = _assignIds((doc.blocks || []).map(_migrateBlock));
    clearDirty();
    _seedHistory();
  }

  /** Replace canvas with a template (array of {type, props?, children?, label?} objects). */
  function loadTemplate(templateBlocks) {
    _pushHistory(true);
    selectedBlockId.value = null;

    function buildFromTemplate(tpl) {
      const type = tpl.type === "rich_text" ? "text" : tpl.type;
      const b = _createBlock(type, nextId());
      if (tpl.label) b.label = tpl.label;
      if (tpl.props) Object.assign(b.props, tpl.props);
      // Recursively build container children
      if (tpl.children?.length) {
        b.children = tpl.children.map(buildFromTemplate);
      }
      // Handle legacy columns blocks
      if (tpl.columns) {
        b.columns = tpl.columns.map(col => ({
          blocks: (col.blocks || []).map(buildFromTemplate),
        }));
      }
      return b;
    }

    blocks.value = templateBlocks.map(buildFromTemplate);
    markDirty();
  }

  return {
    blocks,
    renderedHtml,
    campaignName,
    campaignDoc,
    emailWidth,
    canvasBg,
    selectedBlockId,
    selectedBlockIds,
    selectedBlock,
    isDirty,
    canUndo,
    canRedo,
    undo,
    redo,
    addBlock,
    removeBlock,
    moveBlock,
    selectBlock,
    toggleInSelection,
    addRangeToSelection,
    updateBlockProps,
    updateBlockPropsLive,
    addChildBlock,
    moveChildBlock,
    addBlockToColumn,
    moveBlockInColumn,
    setColumnCount,
    moveBlockTo,
    insertBuiltBlock,
    duplicateBlock,
    copyBlock,
    copyBlocks,
    pasteBlock,
    clipboard,
    styleClipboard,
    copyStyle,
    pasteStyle,
    setBlockLabel,
    setRenderedHtml,
    loadFromDoc,
    loadTemplate,
    findBlock,
    markDirty,
    clearDirty,
    isReadOnly,
    moveBlockToColumn,
  };
});

// ── Block factory ─────────────────────────────────────────────────────────────
function _createBlock(type, id) {
  const schema = BLOCK_SCHEMA[type];
  const defaults = schema?.defaults ?? {};
  const block = {
    id,
    type,
    props: JSON.parse(JSON.stringify(defaults)),
    ...(type === "container" ? { children: [] } : {}),
  };
  if (type === "columns") {
    const count = parseInt(defaults.column_count || "2");
    block.columns = Array.from({ length: count }, () => ({ blocks: [] }));
  }
  return block;
}
