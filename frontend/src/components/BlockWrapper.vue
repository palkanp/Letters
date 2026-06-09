<template>
  <div
    class="relative rounded border-2 transition-colors"
    :class="[
      selected ? 'border-gray-900 shadow-sm' : 'border-transparent hover:border-gray-200',
      isDragOver === 'before' ? 'border-t-blue-500' : '',
      isDragOver === 'after'  ? 'border-b-blue-500' : '',
    ]"
    :style="spacingStyle"
    @click.stop="store.selectBlock(block.id)"
    @dragover.prevent="onDragOver"
    @dragleave="isDragOver = null"
    @drop.prevent="onDrop"
  >

    <!-- ── Drag reorder grip ──────────────────────────────────────────────── -->
    <div
      v-if="selected"
      title="Drag to reorder"
      draggable="true"
      class="absolute top-1/2 -translate-y-1/2 -left-7 w-6 h-8 flex items-center justify-center
             cursor-grab active:cursor-grabbing select-none rounded
             text-gray-300 hover:text-gray-600 hover:bg-gray-100 transition-colors z-10"
      @dragstart="onDragStart"
      @dragend="onDragEnd"
      @click.stop
    >
      <!-- 6-dot grip icon -->
      <svg width="10" height="14" viewBox="0 0 10 14" fill="currentColor">
        <circle cx="2.5" cy="2"  r="1.5"/>
        <circle cx="7.5" cy="2"  r="1.5"/>
        <circle cx="2.5" cy="7"  r="1.5"/>
        <circle cx="7.5" cy="7"  r="1.5"/>
        <circle cx="2.5" cy="12" r="1.5"/>
        <circle cx="7.5" cy="12" r="1.5"/>
      </svg>
    </div>

    <!-- Drop-target lines -->
    <div
      v-if="isDragOver === 'before'"
      class="absolute inset-x-0 -top-px h-0.5 bg-blue-500 rounded-full z-20 pointer-events-none"
    />
    <div
      v-if="isDragOver === 'after'"
      class="absolute inset-x-0 -bottom-px h-0.5 bg-blue-500 rounded-full z-20 pointer-events-none"
    />

    <!-- ── Padding top handle ─────────────────────────────────────────────── -->
    <div
      v-if="selected"
      class="absolute inset-x-6 top-0 h-2.5 cursor-ns-resize z-10 flex items-start justify-center group"
      @pointerdown.prevent.stop="startPaddingDrag('top', $event)"
      @click.stop
    >
      <div class="w-10 h-1 mt-0.5 rounded-full bg-gray-400 opacity-0 group-hover:opacity-60 transition-opacity" />
    </div>

    <!-- ── Padding bottom handle ──────────────────────────────────────────── -->
    <div
      v-if="selected"
      class="absolute inset-x-6 bottom-0 h-2.5 cursor-ns-resize z-10 flex items-end justify-center group"
      @pointerdown.prevent.stop="startPaddingDrag('bottom', $event)"
      @click.stop
    >
      <div class="w-10 h-1 mb-0.5 rounded-full bg-gray-400 opacity-0 group-hover:opacity-60 transition-opacity" />
    </div>

    <!-- ── Padding tooltip ────────────────────────────────────────────────── -->
    <Transition
      enter-active-class="transition-opacity duration-100"
      leave-active-class="transition-opacity duration-100"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div
        v-if="paddingTip"
        class="absolute right-1 top-1 text-xs bg-gray-900 text-white px-1.5 py-0.5 rounded pointer-events-none z-30 font-mono"
      >{{ paddingTip }}</div>
    </Transition>

    <slot />
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useEditorStore } from "../stores/editor";

const props  = defineProps({ block: Object, index: Number });
const store  = useEditorStore();
const selected = computed(() => store.selectedBlockId === props.block.id);

// ── Spacing wrapper style ────────────────────────────────────────────────────
const spacingStyle = computed(() => {
  const t = props.block.props?.spacing_top;
  const b = props.block.props?.spacing_bottom;
  return {
    marginTop:    t != null ? `${t}px` : "4px",
    marginBottom: b != null ? `${b}px` : "4px",
  };
});

// ── Drag-to-reorder ──────────────────────────────────────────────────────────
// Module-level so all instances share the same source
let _dragSourceIndex = null;
const isDragOver = ref(null); // 'before' | 'after' | null

function onDragStart(e) {
  _dragSourceIndex = props.index;
  e.dataTransfer.effectAllowed = "move";
  // Set minimal ghost (transparent 1×1 pixel)
  const ghost = document.createElement("div");
  ghost.style.cssText = "width:1px;height:1px;position:fixed;top:-9999px;";
  document.body.appendChild(ghost);
  e.dataTransfer.setDragImage(ghost, 0, 0);
  setTimeout(() => document.body.removeChild(ghost), 0);
}

function onDragEnd() {
  _dragSourceIndex = null;
  isDragOver.value  = null;
}

function onDragOver(e) {
  if (_dragSourceIndex === null || _dragSourceIndex === props.index) return;
  const rect = e.currentTarget.getBoundingClientRect();
  isDragOver.value = e.clientY < rect.top + rect.height / 2 ? "before" : "after";
}

function onDrop(e) {
  if (_dragSourceIndex === null) return;
  const fromIndex  = _dragSourceIndex;
  const dropBefore = isDragOver.value === "before";
  isDragOver.value = null;

  if (fromIndex === props.index) { _dragSourceIndex = null; return; }

  // Calculate destination index accounting for the removal of the source
  let dest = dropBefore ? props.index : props.index + 1;
  if (fromIndex < dest) dest--; // source removal shifts remaining items left
  store.moveBlock(fromIndex, dest);
  _dragSourceIndex = null;
}

// ── Padding resize handles ───────────────────────────────────────────────────
const paddingTip = ref(null);
let _tipTimer = null;

function showTip(msg) {
  paddingTip.value = msg;
  clearTimeout(_tipTimer);
  _tipTimer = setTimeout(() => (paddingTip.value = null), 1200);
}

const DEFAULT_PADDING = { top: 20, right: 32, bottom: 20, left: 32 };

function startPaddingDrag(edge, e) {
  store.selectBlock(props.block.id);
  e.target.setPointerCapture(e.pointerId);

  const propKey  = `padding_${edge}`;
  const startY   = e.clientY;
  const startVal = parseInt(props.block.props[propKey] ?? DEFAULT_PADDING[edge]);

  function onMove(ev) {
    const delta  = ev.clientY - startY;
    // Top: drag down → more padding (positive delta = bigger)
    // Bottom: drag down → more padding (positive delta = bigger)
    const raw    = startVal + delta;
    const clamped = Math.max(0, Math.round(raw / 4) * 4); // snap to 4px grid
    store.updateBlockProps(props.block.id, { [propKey]: clamped });
    showTip(`${edge === 'top' ? '↑' : '↓'} ${clamped}px`);
  }

  function onUp() {
    e.target.removeEventListener("pointermove", onMove);
    e.target.removeEventListener("pointerup",   onUp);
  }

  e.target.addEventListener("pointermove", onMove);
  e.target.addEventListener("pointerup",   onUp);
}
</script>
