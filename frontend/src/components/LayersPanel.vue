<template>
  <div class="flex flex-col h-full">
    <!-- Empty state -->
    <div
      v-if="!store.blocks.length"
      class="flex-1 flex flex-col items-center justify-center px-4 text-center gap-2"
    >
      <p class="text-xs text-ink-gray-4 leading-relaxed">
        No blocks yet. Use <strong>+ Add block</strong> below.
      </p>
    </div>

    <!-- Layer tree (frappe-ui Tree drives recursion, indent guides + chevrons) -->
    <div
      v-else
      class="flex-1 overflow-y-auto py-1.5 px-1.5"
      @dragover.prevent
      @drop.prevent="onDropAtEnd"
    >
      <Tree
        v-for="block in store.blocks"
        :key="block.id"
        :node="block"
        node-key="id"
        :options="treeOptions"
      >
        <template #node="{ node, hasChildren, isCollapsed, toggleCollapsed }">
          <div
            class="group relative flex items-center gap-1.5 rounded-md px-1 py-0.5 cursor-pointer select-none transition-colors"
            :class="rowClass(node)"
            draggable="true"
            @click.stop="store.selectBlock(node.id)"
            @dblclick.stop="startRename(node.id)"
            @dragstart.stop="onDragStart(node.id, $event)"
            @dragover.stop.prevent="onDragOver(node.id, $event)"
            @drop.stop.prevent="onDrop(node.id)"
            @dragend="clearDrag"
          >
            <!-- Drop indicators: line above (before), ring (inside), line below (after) -->
            <div
              v-if="dropState?.targetId === node.id && dropState.zone === 'before'"
              class="absolute inset-x-1 -top-px h-0.5 bg-blue-500 rounded-full pointer-events-none z-10"
            />
            <div
              v-if="dropState?.targetId === node.id && dropState.zone === 'inside'"
              class="absolute inset-0 rounded-md ring-2 ring-blue-400 bg-blue-50/40 pointer-events-none z-10"
            />
            <div
              v-if="dropState?.targetId === node.id && dropState.zone === 'after'"
              class="absolute inset-x-1 -bottom-px h-0.5 bg-blue-500 rounded-full pointer-events-none z-10"
            />

            <!-- Chevron (containers) or alignment spacer (leaves) -->
            <button
              v-if="hasChildren"
              type="button"
              class="flex-shrink-0 w-4 h-4 flex items-center justify-center text-ink-gray-5 hover:text-ink-gray-8"
              :aria-label="isCollapsed ? 'Expand' : 'Collapse'"
              @click.stop="toggleCollapsed"
            >
              <FeatherIcon :name="isCollapsed ? 'chevron-right' : 'chevron-down'" class="w-3.5 h-3.5" />
            </button>
            <span v-else class="flex-shrink-0 w-4" />

            <!-- Block-type icon (structural blocks get a colour accent) -->
            <FeatherIcon
              :name="blockIcon(node.type)"
              class="w-3.5 h-3.5 flex-shrink-0"
              :class="iconClass(node)"
            />

            <!-- Label — inline editable on double-click -->
            <input
              v-if="editingId === node.id"
              v-focus
              class="flex-1 text-xs bg-transparent border-b border-blue-400 outline-none min-w-0 py-0.5"
              :value="node.label || blockLabel(node.type)"
              @blur="finishRename(node.id, $event.target.value)"
              @keydown.enter.prevent="finishRename(node.id, $event.target.value)"
              @keydown.esc.prevent="editingId = null"
              @click.stop
              @dblclick.stop
              @dragstart.stop.prevent
            />
            <span
              v-else
              class="flex-1 text-xs truncate"
              :class="isStructural(node.type) ? 'font-medium text-ink-gray-8' : ''"
            >{{ node.label || blockLabel(node.type) }}</span>

            <!-- Index badge (top-level only) -->
            <span
              v-if="topLevelIndex(node.id) !== null"
              class="text-xs text-ink-gray-3 flex-shrink-0 tabular-nums px-0.5"
            >{{ topLevelIndex(node.id) + 1 }}</span>

            <!-- Add inside (containers only) -->
            <button
              v-if="node.type === 'container'"
              type="button"
              class="opacity-0 group-hover:opacity-100 text-ink-gray-5 hover:text-blue-600 transition flex-shrink-0 w-4 h-4 flex items-center justify-center rounded hover:bg-blue-50"
              title="Add block inside"
              aria-label="Add block inside container"
              @click.stop="openPicker({ mode: 'child', parentId: node.id, afterIndex: (node.children?.length ?? 1) - 1 })"
            ><FeatherIcon name="plus" class="w-3 h-3" /></button>

            <!-- Remove -->
            <button
              type="button"
              class="opacity-0 group-hover:opacity-100 text-ink-gray-4 hover:text-red-500 transition flex-shrink-0 w-4 h-4 flex items-center justify-center rounded"
              title="Remove"
              aria-label="Remove block"
              @click.stop="store.removeBlock(node.id)"
            ><FeatherIcon name="x" class="w-3 h-3" /></button>
          </div>
        </template>
      </Tree>
    </div>

    <!-- Reorder hint -->
    <div v-if="store.blocks.length > 1" class="px-3 py-2 border-t border-gray-100">
      <p class="text-xs text-ink-gray-3 text-center">Drag to reorder · double-click to rename</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject } from "vue";
import { Tree, FeatherIcon } from "frappe-ui";
import { useEditorStore } from "../stores/editor";
import { BLOCK_SCHEMA } from "../blockSchema";

const store = useEditorStore();
const openPicker = inject("openPicker", () => {});

// Focus the rename input the moment it mounts (native autofocus doesn't fire on
// v-if insertion).
const vFocus = { mounted: (el) => el.focus() };

const treeOptions = {
  rowHeight: "32px",
  indentWidth: "16px",
  showIndentationGuides: true,
  defaultCollapsed: false,
};

// Structural blocks (grouping containers) are visually emphasised so the
// hierarchy reads at a glance — the equivalent of Builder's bold/accent rows.
const STRUCTURAL = new Set(["container", "columns"]);
const isStructural = (type) => STRUCTURAL.has(type);

const blockIcon = (type) => BLOCK_SCHEMA[type]?.icon || "box";
const blockLabel = (type) => BLOCK_SCHEMA[type]?.label || type;

function rowClass(node) {
  if (store.selectedBlockId === node.id) return "bg-surface-gray-2 text-ink-gray-9";
  return "text-ink-gray-7 hover:bg-surface-gray-2";
}

function iconClass(node) {
  return store.selectedBlockId === node.id ? "text-ink-gray-7" : "text-ink-gray-4";
}

// ── Block metadata: id -> { parentId, index, childrenCount, isContainer } ─────
// Drives both the index badge and position-aware drops without needing a flat
// index into a rendered list.
const blockMeta = computed(() => {
  const map = new Map();
  function walk(list, parentId) {
    list.forEach((block, index) => {
      map.set(block.id, {
        parentId,
        index,
        childrenCount: block.children?.length ?? 0,
        isContainer: block.type === "container",
      });
      if (block.children?.length) walk(block.children, block.id);
    });
  }
  walk(store.blocks, null);
  return map;
});

function topLevelIndex(id) {
  const m = blockMeta.value.get(id);
  return m && m.parentId === null ? m.index : null;
}

// ── Drag-to-reorder (cross-level, position-aware) ────────────────────────────
// dropState: { targetId, zone: 'before' | 'inside' | 'after' } | null
const dragId    = ref(null);
const dropState = ref(null);

function onDragStart(id, e) {
  dragId.value = id;
  e.dataTransfer.effectAllowed = "move";
}

function getZone(e, isContainer) {
  const rect = e.currentTarget.getBoundingClientRect();
  const ratio = (e.clientY - rect.top) / rect.height;
  if (!isContainer) return ratio < 0.5 ? "before" : "after";
  // Container: top 30% = before, middle 40% = inside, bottom 30% = after
  if (ratio < 0.3) return "before";
  if (ratio < 0.7) return "inside";
  return "after";
}

// True when `nodeId` sits inside `ancestorId`'s subtree — used to forbid
// dropping a block into its own descendant (which would detach the subtree).
function isDescendant(ancestorId, nodeId) {
  let cur = blockMeta.value.get(nodeId);
  while (cur && cur.parentId != null) {
    if (cur.parentId === ancestorId) return true;
    cur = blockMeta.value.get(cur.parentId);
  }
  return false;
}

function onDragOver(id, e) {
  if (dragId.value == null || dragId.value === id || isDescendant(dragId.value, id)) {
    dropState.value = null;
    return;
  }
  const meta = blockMeta.value.get(id);
  dropState.value = { targetId: id, zone: getZone(e, meta?.isContainer) };
}

function onDrop(id) {
  const from  = dragId.value;
  const state = dropState.value;
  clearDrag();
  if (from == null || from === id || !state || isDescendant(from, id)) return;

  const meta = blockMeta.value.get(id);
  if (!meta) return;
  const { zone } = state;

  if (zone === "inside" && meta.isContainer) {
    store.moveBlockTo(from, id, meta.childrenCount); // append as last child
  } else if (zone === "before") {
    store.moveBlockTo(from, meta.parentId, meta.index);
  } else {
    store.moveBlockTo(from, meta.parentId, meta.index + 1);
  }
}

function onDropAtEnd() {
  const from = dragId.value;
  clearDrag();
  if (from == null) return;
  store.moveBlockTo(from, null, store.blocks.length);
}

function clearDrag() {
  dragId.value    = null;
  dropState.value = null;
}

// ── Inline rename ─────────────────────────────────────────────────────────────
const editingId = ref(null);
const startRename  = (id) => { editingId.value = id; };
function finishRename(id, value) {
  store.setBlockLabel(id, value);
  editingId.value = null;
}
</script>
