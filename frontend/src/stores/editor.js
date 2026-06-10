import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { BLOCK_SCHEMA } from "../blockSchema";

export const useEditorStore = defineStore("editor", () => {
  const blocks         = ref([]);
  const renderedHtml   = ref("");
  const campaignName   = ref("");
  const campaignDoc    = ref(null);
  const selectedBlockId = ref(null);
  const isDirty        = ref(false);

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

  function _pushHistory() {
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
    _pushHistory();
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
    _pushHistory();
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
    _pushHistory();
    const item = blocks.value.splice(fromIndex, 1)[0];
    blocks.value.splice(toIndex, 0, item);
    markDirty();
  }

  function selectBlock(id) {
    selectedBlockId.value = id;
  }

  function updateBlockProps(id, props) {
    _pushHistory();
    const block = findBlock(id);
    if (block) { Object.assign(block.props, props); markDirty(); }
  }

  // ── Container child operations ───────────────────────────────────────────────
  function addChildBlock(parentId, type, afterIndex = null) {
    _pushHistory();
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
    _pushHistory();
    const parent = findBlock(parentId);
    if (!parent?.children) return;
    const item = parent.children.splice(fromIndex, 1)[0];
    parent.children.splice(toIndex, 0, item);
    markDirty();
  }

  // ── Columns child operations ─────────────────────────────────────────────────
  function addBlockToColumn(blockId, colIndex, type, afterIndex = null) {
    _pushHistory();
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
    _pushHistory();
    const block = findBlock(blockId);
    const col = block?.columns?.[colIndex];
    if (!col?.blocks) return;
    const item = col.blocks.splice(fromIndex, 1)[0];
    col.blocks.splice(toIndex, 0, item);
    markDirty();
  }

  function setColumnCount(blockId, count) {
    _pushHistory();
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
    _pushHistory();
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
    _pushHistory();
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

  function setBlockLabel(id, label) {
    _pushHistory();
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

  function loadFromDoc(doc) {
    campaignDoc.value  = doc;
    campaignName.value = doc.title;
    _idCounter.value   = 0;
    selectedBlockId.value = null;
    blocks.value = _assignIds(doc.blocks || []);
    clearDirty();
    _seedHistory();
  }

  /** Replace canvas with a template (array of {type, props?} objects). */
  function loadTemplate(templateBlocks) {
    _pushHistory();
    selectedBlockId.value = null;
    // Use _createBlock defaults then merge any provided props
    blocks.value = templateBlocks.map((tpl) => {
      const b = _createBlock(tpl.type, nextId());
      if (tpl.props) Object.assign(b.props, tpl.props);
      if (tpl.type === "columns" && tpl.columns) {
        b.columns = tpl.columns.map(col => ({
          blocks: (col.blocks || []).map(cb => {
            const child = _createBlock(cb.type, nextId());
            if (cb.props) Object.assign(child.props, cb.props);
            return child;
          }),
        }));
      }
      return b;
    });
    markDirty();
  }

  return {
    blocks,
    renderedHtml,
    campaignName,
    campaignDoc,
    selectedBlockId,
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
    updateBlockProps,
    addChildBlock,
    moveChildBlock,
    addBlockToColumn,
    moveBlockInColumn,
    setColumnCount,
    moveBlockTo,
    duplicateBlock,
    setBlockLabel,
    setRenderedHtml,
    loadFromDoc,
    loadTemplate,
    findBlock,
    markDirty,
    clearDirty,
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
