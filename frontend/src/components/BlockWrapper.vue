<template>
  <div
    class="relative transition-colors group/block"
    :class="[
      isDragOver === 'before' ? 'border-t-2 border-t-blue-500' : '',
      isDragOver === 'after'  ? 'border-b-2 border-b-blue-500' : '',
    ]"
    :style="{
      ...spacingStyle, ...props.extraStyle,
      ...blockBorderStyle,
    }"
    :data-block-id="block.id"
    @mouseenter="isHovered = true"
    @mouseleave="isHovered = false"
    @click.stop="store.selectBlock(block.id)"
    @dragover.prevent="onDragOver"
    @dragleave="isDragOver = null"
    @drop.prevent="onDrop"
  >

    <!-- ── Drag reorder grip (top-level blocks only) ───────────────────── -->
    <div
      v-if="isTopLevel"
      title="Drag to reorder"
      draggable="true"
      class="absolute top-1/2 -translate-y-1/2 -left-7 w-6 h-8 flex items-center justify-center
             cursor-grab active:cursor-grabbing select-none rounded
             text-ink-gray-3 hover:text-ink-gray-7 hover:bg-surface-gray-3 transition-all z-10
             opacity-0 group-hover/block:opacity-100"
      :class="selected ? 'opacity-100' : ''"
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

    <!-- ── Padding left handle ───────────────────────────────────────────── -->
    <div
      v-if="selected"
      class="absolute inset-y-6 left-0 w-2.5 cursor-ew-resize z-10 flex items-center justify-start group"
      @pointerdown.prevent.stop="startPaddingDragH('left', $event)"
      @click.stop
    >
      <div class="h-10 w-1 ml-0.5 rounded-full bg-gray-400 opacity-0 group-hover:opacity-60 transition-opacity" />
    </div>

    <!-- ── Padding right handle ──────────────────────────────────────────── -->
    <div
      v-if="selected"
      class="absolute inset-y-6 right-0 w-2.5 cursor-ew-resize z-10 flex items-center justify-end group"
      @pointerdown.prevent.stop="startPaddingDragH('right', $event)"
      @click.stop
    >
      <div class="h-10 w-1 mr-0.5 rounded-full bg-gray-400 opacity-0 group-hover:opacity-60 transition-opacity" />
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
        class="absolute right-1 top-1 text-xs bg-surface-gray-7 text-ink-white px-1.5 py-0.5 rounded pointer-events-none z-30 font-mono"
      >{{ paddingTip }}</div>
    </Transition>

    <!-- Inner content wrapper: clips to border-radius without hiding the drag grip.
         Also carries the width constraint so the outer div's background fills the full row. -->
    <div :style="{ ...contentClipStyle, ...topLevelContainerStyle }">
      <slot />
    </div>

    <!-- Selection / hover ring — absolute overlay so it always renders above content backgrounds -->
    <div
      v-if="selected || (isHovered && !store.selectedBlockId)"
      class="absolute inset-0 pointer-events-none z-20"
      :style="{
        boxShadow: selected ? 'inset 0 0 0 2px #3b82f6' : 'inset 0 0 0 1.5px #bfdbfe',
        borderRadius: blockBorderStyle.borderRadius,
      }"
    />
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useEditorStore } from "../stores/editor";

const props  = defineProps({ block: Object, index: Number, extraStyle: { type: Object, default: () => ({}) } });
const store  = useEditorStore();
const selected  = computed(() => store.selectedBlockId === props.block.id);
const isHovered = ref(false);

// Only top-level blocks (directly in store.blocks) support drag-to-reorder.
// Child blocks inside containers should not interfere with the top-level order.
const isTopLevel = computed(() => store.blocks.some((b) => b.id === props.block.id));

// ── Block-level border + corner radius ───────────────────────────────────────
const blockBorderStyle = computed(() => {
  const c = props.block.props?.block_border_color;
  const r = props.block.props?.block_border_radius;
  return {
    border: c ? `1px solid ${c}` : "none",
    borderRadius: r || "0",
  };
});

// Inner content wrapper clips block content to the border-radius.
// The outer div stays overflow:visible so the drag grip (at -left-7) isn't clipped.
const contentClipStyle = computed(() => {
  const r = props.block.props?.block_border_radius;
  if (!r || r === "0") return {};
  return { overflow: "hidden", borderRadius: r };
});

// ── Top-level container width + alignment ────────────────────────────────────
// Width is only applied here when the container is top-level (not inside another
// container's childFlexStyle). Child containers get their width via the parent's
// childFlexStyle to avoid double-application (% of % bug).
const topLevelContainerStyle = computed(() => {
  if (props.block.type !== "container" || !isTopLevel.value) return {};
  const w = props.block.props?.width;
  const a = props.block.props?.align;
  const hasCustomWidth = w && w !== "100%" && w !== "auto" && w !== "0px";
  if (!hasCustomWidth) return {};
  const marginMap = { left: "0 auto 0 0", center: "0 auto", right: "0 0 0 auto" };
  return {
    width: w,
    ...(a && a !== "left" ? { margin: marginMap[a] } : {}),
  };
});

// ── Spacing wrapper style ────────────────────────────────────────────────────
// Use padding (not margin) so the gap inherits the block's own background color
// instead of exposing the canvas surface color.
const spacingStyle = computed(() => {
  const t  = props.block.props?.spacing_top  ?? 0;
  const b  = props.block.props?.spacing_bottom ?? 0;
  const bg = props.block.props?.background_color;
  const hasBg = bg && bg !== "transparent";
  return {
    paddingTop:      t > 0 ? `${t}px` : undefined,
    paddingBottom:   b > 0 ? `${b}px` : undefined,
    backgroundColor: (t > 0 || b > 0) && hasBg ? bg : undefined,
  };
});

// ── Drag-to-reorder ──────────────────────────────────────────────────────────
// _dragSourceIndex is intentionally module-level (not reactive ref) so that all
// BlockWrapper instances share a single drag source at a time. Only one top-level
// block can be dragged at once, so this is safe and avoids cross-instance state.
let _dragSourceIndex = null;
const isDragOver = ref(null); // 'before' | 'after' | null

function onDragStart(e) {
  if (!isTopLevel.value) return;
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
  if (!isTopLevel.value) return;
  if (_dragSourceIndex === null || _dragSourceIndex === props.index) return;
  const rect = e.currentTarget.getBoundingClientRect();
  isDragOver.value = e.clientY < rect.top + rect.height / 2 ? "before" : "after";
}

function onDrop(e) {
  if (!isTopLevel.value || _dragSourceIndex === null) return;
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

const DEFAULT_PADDING = { top: 20, right: 16, bottom: 20, left: 16 };

function startPaddingDrag(edge, e) {
  store.selectBlock(props.block.id);
  e.target.setPointerCapture(e.pointerId);

  const propKey  = `padding_${edge}`;
  const startY   = e.clientY;
  const startVal = parseInt(props.block.props[propKey] ?? DEFAULT_PADDING[edge]);

  // Snapshot history once at drag start so undo restores the full drag in one step
  store.updateBlockProps(props.block.id, { [propKey]: startVal });

  function onMove(ev) {
    const delta   = ev.clientY - startY;
    const raw     = startVal + delta;
    const clamped = Math.max(0, Math.round(raw / 4) * 4);
    store.updateBlockPropsLive(props.block.id, { [propKey]: clamped });
    showTip(`${edge === 'top' ? '↑' : '↓'} ${clamped}px`);
  }

  function onUp() {
    e.target.removeEventListener("pointermove", onMove);
    e.target.removeEventListener("pointerup",   onUp);
  }

  e.target.addEventListener("pointermove", onMove);
  e.target.addEventListener("pointerup",   onUp);
}

// Horizontal drag for left / right padding
function startPaddingDragH(edge, e) {
  store.selectBlock(props.block.id);
  e.target.setPointerCapture(e.pointerId);

  const propKey  = `padding_${edge}`;
  const startX   = e.clientX;
  const startVal = parseInt(props.block.props[propKey] ?? DEFAULT_PADDING[edge]);

  // Snapshot history once at drag start
  store.updateBlockProps(props.block.id, { [propKey]: startVal });

  function onMove(ev) {
    const delta   = ev.clientX - startX;
    const sign    = edge === "left" ? 1 : -1;
    const raw     = startVal + sign * delta;
    const clamped = Math.max(0, Math.round(raw / 4) * 4);
    store.updateBlockPropsLive(props.block.id, { [propKey]: clamped });
    showTip(`${edge === 'left' ? '←' : '→'} ${clamped}px`);
  }

  function onUp() {
    e.target.removeEventListener("pointermove", onMove);
    e.target.removeEventListener("pointerup",   onUp);
  }

  e.target.addEventListener("pointermove", onMove);
  e.target.addEventListener("pointerup",   onUp);
}
</script>
