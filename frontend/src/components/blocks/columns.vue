<template>
  <BlockWrapper :block="block" :index="index">
    <div :style="{ backgroundColor: block.props.background_color || '#ffffff', ...paddingStyle }">
      <div class="flex" :style="{ gap: `${block.props.col_gap ?? 24}px`, alignItems: block.props.vertical_align || 'stretch' }">
        <div
          v-for="(col, colIdx) in block.columns || []"
          :key="colIdx"
          class="flex-1 min-w-0 flex flex-col"
          :style="colBorderStyle(colIdx)"
        >
          <!-- Child blocks inside this column -->
          <div
            v-for="(child, childIdx) in col.blocks || []"
            :key="child.id"
            class="relative group/colchild"
            draggable="true"
            @click.stop="store.selectBlock(child.id)"
            @dragstart.stop="onDragStart(colIdx, childIdx, $event)"
            @dragover.stop.prevent="onDragOver(colIdx, childIdx)"
            @dragleave.stop="dragOver = null"
            @drop.stop.prevent="onDrop(colIdx, childIdx)"
            @dragend.stop="dragFrom = null; dragOver = null"
          >
            <!-- Drop indicator -->
            <div
              v-if="dragOver?.col === colIdx && dragOver?.idx === childIdx && dragFrom !== null"
              class="absolute inset-x-0 -top-px h-0.5 bg-blue-500 rounded-full pointer-events-none z-20"
            />
            <!-- Selection ring -->
            <div
              class="absolute inset-0 rounded pointer-events-none z-10 transition-all"
              :class="store.selectedBlockId === child.id
                ? 'ring-2 ring-blue-400 ring-offset-1'
                : 'group-hover/colchild:ring-1 group-hover/colchild:ring-blue-200'"
            />
            <!-- Remove child button -->
            <button
              type="button"
              class="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-surface-base border border-outline-gray-2
                     shadow-sm text-ink-gray-4 hover:text-red-500 hover:border-red-200 text-xs
                     leading-none z-20 opacity-0 group-hover/colchild:opacity-100 transition-opacity
                     flex items-center justify-center"
              title="Remove block"
              @click.stop="store.removeBlock(child.id)"
            ><FeatherIcon name="x" class="w-3 h-3" /></button>
            <!-- Actual block -->
            <BlockRenderer :block="child" :index="childIdx" />
          </div>

          <!-- Empty column placeholder -->
          <div
            v-if="!col.blocks?.length"
            class="flex-1 flex items-center justify-center py-6 border-2 border-dashed border-outline-gray-2 rounded-lg text-ink-gray-3 text-xs select-none"
          >Empty column</div>

          <!-- Add block to this column -->
          <button
            v-if="store.selectedBlockId === block.id || isChildSelected(col)"
            type="button"
            class="mt-2 w-full flex items-center justify-center gap-1 py-1.5 rounded-lg
                   border border-dashed border-outline-gray-2 text-xs text-ink-gray-4
                   hover:border-outline-gray-4 hover:text-ink-gray-6 transition-colors"
            @click.stop="addToColumn(colIdx)"
          >
            <FeatherIcon name="plus" class="w-3 h-3" /> Add block
          </button>
        </div>
      </div>
    </div>
  </BlockWrapper>
</template>

<script setup>
import { computed, ref, watch, inject } from "vue";
import { FeatherIcon } from "frappe-ui";
import BlockWrapper from "../BlockWrapper.vue";
import BlockRenderer from "../BlockRenderer.vue";
import { useEditorStore } from "../../stores/editor";
import { usePadding } from "../../composables/usePadding";

const props  = defineProps({ block: Object, index: Number });
const store  = useEditorStore();
const openPicker = inject("openPicker");

const blockProps   = computed(() => props.block.props);
const paddingStyle = usePadding(blockProps, { top: 20, right: 24, bottom: 20, left: 24 });

// ── Sync column_count → columns array ────────────────────────────────────────
watch(
  () => props.block.props.column_count,
  (val, oldVal) => {
    const count    = parseInt(val)    || 2;
    const oldCount = parseInt(oldVal) || 2;
    if (count >= oldCount) { store.setColumnCount(props.block.id, count); return; }

    // Reducing: check if any columns being removed have content.
    const cols = props.block.columns || [];
    const hasContent = cols.slice(count).some((col) => col.blocks?.length > 0);
    if (hasContent) {
      const ok = window.confirm(
        `Reducing to ${count} column${count === 1 ? "" : "s"} will delete the content in the removed column${count === oldCount - 1 ? "" : "s"}. Continue?`
      );
      if (!ok) {
        // Revert the prop change in the store without triggering the watcher again.
        store.updateBlockPropsLive(props.block.id, { column_count: oldCount });
        return;
      }
    }
    store.setColumnCount(props.block.id, count);
  },
);

// ── Column divider border ─────────────────────────────────────────────────────
function colBorderStyle(colIdx) {
  const last = (props.block.columns?.length ?? 1) - 1;
  if (!props.block.props.show_dividers || colIdx === last) return {};
  return {
    borderRight: `1px solid ${props.block.props.divider_color || "#e5e7eb"}`,
    paddingRight: `${Math.round((props.block.props.col_gap ?? 24) / 2)}px`,
    marginRight: `-${Math.round((props.block.props.col_gap ?? 24) / 2)}px`,
  };
}

// ── Check if any child in a column is selected (to show add button) ──────────
function isChildSelected(col) {
  return (col.blocks || []).some(b => store.selectedBlockId === b.id);
}

// ── Add block to specific column via the block picker ────────────────────────
function addToColumn(colIdx) {
  openPicker({
    mode: "column",
    blockId: props.block.id,
    colIndex: colIdx,
    afterIndex: (props.block.columns?.[colIdx]?.blocks?.length ?? 0) - 1,
  });
}

// ── Drag-to-reorder within a column ──────────────────────────────────────────
const dragFrom = ref(null); // { col, idx }
const dragOver  = ref(null); // { col, idx }

function onDragStart(colIdx, childIdx, e) {
  dragFrom.value = { col: colIdx, idx: childIdx };
  e.dataTransfer.effectAllowed = "move";
}
function onDragOver(colIdx, childIdx) {
  if (dragFrom.value === null) return;
  dragOver.value = { col: colIdx, idx: childIdx };
}
function onDrop(colIdx, childIdx) {
  const from = dragFrom.value;
  dragFrom.value = null;
  dragOver.value = null;
  if (!from || from.col !== colIdx || from.idx === childIdx) return;
  store.moveBlockInColumn(props.block.id, colIdx, from.idx, childIdx);
}
</script>
