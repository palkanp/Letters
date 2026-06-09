<template>
  <div class="flex flex-col h-full">
    <!-- Empty state -->
    <div
      v-if="!store.blocks.length"
      class="flex-1 flex flex-col items-center justify-center px-4 text-center gap-2"
    >
      <p class="text-xs text-gray-400 leading-relaxed">
        No blocks yet. Use <strong>+ Add block</strong> below.
      </p>
    </div>

    <!-- Layer rows (flat tree, all depths) -->
    <ul v-else class="flex-1 overflow-y-auto py-1.5" @dragover.prevent @drop.prevent="onDropAtEnd">
      <li
        v-for="(item, flatIdx) in flatTree"
        :key="item.block.id"
        class="relative flex items-center gap-1.5 mr-2 my-0.5 px-2 py-1.5 rounded-lg cursor-pointer transition-colors select-none group"
        :style="{ paddingLeft: `${8 + item.depth * 16}px` }"
        :class="store.selectedBlockId === item.block.id
          ? 'bg-blue-50 text-blue-700'
          : item.depth === 0 ? 'text-gray-600 hover:bg-gray-100' : 'text-gray-500 hover:bg-gray-100'"
        draggable="true"
        @click="store.selectBlock(item.block.id)"
        @dblclick.stop="startRename(item.block.id)"
        @dragstart="onDragStart(flatIdx, $event)"
        @dragover.stop.prevent="onDragOver(flatIdx, $event)"
        @dragleave.stop="onDragLeave(flatIdx, $event)"
        @drop.stop.prevent="onDrop(flatIdx, $event)"
        @dragend="clearDrag"
      >
        <!-- Drop indicators: line above (before), ring (inside), line below (after) -->
        <div
          v-if="dropState?.flatIdx === flatIdx && dropState.zone === 'before'"
          class="absolute inset-x-2 -top-px h-0.5 bg-blue-500 rounded-full pointer-events-none z-10"
        />
        <div
          v-if="dropState?.flatIdx === flatIdx && dropState.zone === 'inside'"
          class="absolute inset-0 rounded-lg ring-2 ring-blue-400 bg-blue-50/40 pointer-events-none z-10"
        />
        <div
          v-if="dropState?.flatIdx === flatIdx && dropState.zone === 'after'"
          class="absolute inset-x-2 -bottom-px h-0.5 bg-blue-500 rounded-full pointer-events-none z-10"
        />

        <!-- Tree connector line for indented items -->
        <div
          v-if="item.depth > 0"
          class="absolute top-0 bottom-0 w-px bg-gray-200 pointer-events-none"
          :style="{ left: `${8 + (item.depth - 1) * 16 + 8}px` }"
        />

        <!-- Drag grip -->
        <span class="text-gray-300 group-hover:text-gray-400 cursor-grab active:cursor-grabbing text-sm leading-none flex-shrink-0" title="Drag to reorder">⠿</span>

        <!-- Block icon -->
        <FeatherIcon :name="blockIcon(item.block.type)" class="w-3 h-3 flex-shrink-0" :class="item.depth > 0 ? 'opacity-60' : ''" />

        <!-- Label — inline editable on double-click -->
        <input
          v-if="editingId === item.block.id"
          autofocus
          class="flex-1 text-xs bg-transparent border-b border-blue-400 outline-none min-w-0 py-0.5"
          :value="item.block.label || blockLabel(item.block.type)"
          @blur="finishRename(item.block.id, $event.target.value)"
          @keydown.enter.prevent="finishRename(item.block.id, $event.target.value)"
          @keydown.esc.prevent="editingId = null"
          @click.stop
          @dblclick.stop
          @dragstart.stop.prevent
        />
        <span v-else class="flex-1 text-xs font-medium truncate">
          {{ item.block.label || blockLabel(item.block.type) }}
        </span>

        <!-- Index badge (top-level only) -->
        <span v-if="item.depth === 0" class="text-xs text-gray-300 flex-shrink-0 tabular-nums">{{ item.index + 1 }}</span>

        <!-- Add inside (containers only) -->
        <button
          v-if="item.block.type === 'container'"
          type="button"
          class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-blue-500 transition-all text-sm leading-none flex-shrink-0 w-4 h-4 flex items-center justify-center rounded hover:bg-blue-50"
          title="Add block inside"
          @click.stop="openPicker({ mode: 'child', parentId: item.block.id, afterIndex: (item.block.children?.length ?? 1) - 1 })"
        >+</button>

        <!-- Remove -->
        <button
          type="button"
          class="opacity-0 group-hover:opacity-100 text-gray-300 hover:text-red-500 transition-all text-xs leading-none flex-shrink-0 w-4 h-4 flex items-center justify-center rounded"
          title="Remove"
          @click.stop="store.removeBlock(item.block.id)"
        >✕</button>
      </li>
    </ul>

    <!-- Reorder hint -->
    <div v-if="store.blocks.length > 1" class="px-3 py-2 border-t border-gray-100">
      <p class="text-xs text-gray-300 text-center">Drag to reorder · double-click to rename</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject } from "vue";
import { FeatherIcon } from "frappe-ui";
import { useEditorStore } from "../stores/editor";
import { BLOCK_SCHEMA } from "../blockSchema";

const store = useEditorStore();
const openPicker = inject("openPicker", () => {});

// ── Flat tree (all depths) ────────────────────────────────────────────────────
const flatTree = computed(() => {
  const result = [];
  function walk(list, depth, parentId) {
    list.forEach((block, index) => {
      result.push({ block, depth, parentId, index });
      if (block.children?.length) {
        walk(block.children, depth + 1, block.id);
      }
    });
  }
  walk(store.blocks, 0, null);
  return result;
});

function blockIcon(type) {
  return BLOCK_SCHEMA[type]?.icon || "box";
}
function blockLabel(type) {
  return BLOCK_SCHEMA[type]?.label || type;
}

// ── Drag-to-reorder (cross-level, position-aware) ────────────────────────────
// dropState: { flatIdx, zone: 'before' | 'inside' | 'after' } | null
const dragFlatIdx = ref(null);
const dropState   = ref(null);

function onDragStart(flatIdx, e) {
  dragFlatIdx.value = flatIdx;
  e.dataTransfer.effectAllowed = "move";
}

function getZone(e, isContainer) {
  const rect = e.currentTarget.getBoundingClientRect();
  const ratio = (e.clientY - rect.top) / rect.height;
  if (!isContainer) {
    return ratio < 0.5 ? "before" : "after";
  }
  // Container: top 30% = before, middle 40% = inside, bottom 30% = after
  if (ratio < 0.3) return "before";
  if (ratio < 0.7) return "inside";
  return "after";
}

function onDragOver(flatIdx, e) {
  if (dragFlatIdx.value === null) return;
  const item = flatTree.value[flatIdx];
  if (!item) return;
  // Don't allow dropping onto self
  if (dragFlatIdx.value === flatIdx) { dropState.value = null; return; }
  const zone = getZone(e, item.block.type === "container");
  dropState.value = { flatIdx, zone };
}

function onDragLeave(flatIdx, e) {
  // Intentionally empty — dropState is updated continuously by onDragOver
  // and cleared by clearDrag (called on dragend / drop).  Clearing here causes
  // the indicator to vanish when the pointer crosses a child element boundary,
  // which makes the drop silently fail.
}

function onDrop(flatIdx, e) {
  const fromIdx = dragFlatIdx.value;
  const state   = dropState.value;
  clearDrag();
  if (fromIdx === null || fromIdx === flatIdx || !state) return;

  const src = flatTree.value[fromIdx];
  const dst = flatTree.value[flatIdx];
  if (!src || !dst) return;

  const { zone } = state;

  if (zone === "inside" && dst.block.type === "container") {
    // Place as last child of this container
    store.moveBlockTo(src.block.id, dst.block.id, dst.block.children?.length ?? 0);
  } else if (zone === "before") {
    // Place before dst in dst's parent
    store.moveBlockTo(src.block.id, dst.parentId, dst.index);
  } else {
    // "after" — place after dst in dst's parent
    store.moveBlockTo(src.block.id, dst.parentId, dst.index + 1);
  }
}

function onDropAtEnd() {
  const fromIdx = dragFlatIdx.value;
  clearDrag();
  if (fromIdx === null) return;
  const src = flatTree.value[fromIdx];
  if (!src) return;
  store.moveBlockTo(src.block.id, null, store.blocks.length);
}

function clearDrag() {
  dragFlatIdx.value = null;
  dropState.value   = null;
}

// ── Inline rename ─────────────────────────────────────────────────────────────
const editingId = ref(null);

function startRename(id) {
  editingId.value = id;
}

function finishRename(id, value) {
  store.setBlockLabel(id, value);
  editingId.value = null;
}
</script>
