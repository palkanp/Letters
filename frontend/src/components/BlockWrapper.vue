<template>
  <div
    class="relative transition-colors group/block"
    :style="{
      ...spacingStyle, ...props.extraStyle,
      ...blockBorderStyle, ...blockSizeStyle,
    }"
    :data-block-id="block.id"
    @mouseenter="isHovered = true"
    @mouseleave="isHovered = false"
    @click.stop="store.selectBlock(block.id)"
  >
    <!-- Inner content (slot first so handles render above it in z-order) -->
    <div :style="{ ...contentClipStyle, ...topLevelContainerStyle }">
      <slot />
    </div>

    <!-- ── All handles come AFTER slot so they stack above content ──────── -->

    <!-- Selection / hover ring — inset to exclude spacing zones -->
    <div
      v-if="selected || (isHovered && !store.selectedBlockId)"
      class="absolute pointer-events-none z-20"
      :style="{
        top:    `${spacingTop}px`,
        bottom: `${spacingBottom}px`,
        left:   0,
        right:  0,
        boxShadow: selected ? 'inset 0 0 0 2px #3b82f6' : 'inset 0 0 0 1.5px #bfdbfe',
        borderRadius: blockBorderStyle.borderRadius,
      }"
    />

    <!-- ── Spacing bands (orange) — always visible; expands + shows value when > 0 ── -->
    <!-- Top: always at least 10px tall so it's draggable even at spacing=0 -->
    <div
      v-if="selected"
      class="absolute inset-x-0 top-0 flex items-center justify-center cursor-ns-resize z-30 select-none group/sp"
      :style="{ height: `${Math.max(10, spacingTop)}px` }"
      @pointerdown.prevent.stop="startSpacingDrag('top', $event)"
      @click.stop
    >
      <div class="absolute inset-0 bg-orange-400 opacity-30 group-hover/sp:opacity-50 transition-opacity" />
      <span class="relative text-[10px] font-mono text-orange-800 font-semibold z-10 pointer-events-none bg-white/80 px-1 rounded leading-tight">
        {{ spacingTop > 0 ? `${spacingTop}px` : '↕' }}
      </span>
    </div>
    <!-- Bottom -->
    <div
      v-if="selected"
      class="absolute inset-x-0 bottom-0 flex items-center justify-center cursor-ns-resize z-30 select-none group/sp"
      :style="{ height: `${Math.max(10, spacingBottom)}px` }"
      @pointerdown.prevent.stop="startSpacingDrag('bottom', $event)"
      @click.stop
    >
      <div class="absolute inset-0 bg-orange-400 opacity-30 group-hover/sp:opacity-50 transition-opacity" />
      <span class="relative text-[10px] font-mono text-orange-800 font-semibold z-10 pointer-events-none bg-white/80 px-1 rounded leading-tight">
        {{ spacingBottom > 0 ? `${spacingBottom}px` : '↕' }}
      </span>
    </div>

    <!-- ── Padding handles (purple) — z-30 so they're above content ──────── -->
    <!-- Top padding -->
    <div
      v-if="selected"
      class="absolute inset-x-8 z-30 flex items-center justify-center cursor-ns-resize group/pad"
      :style="{ top: `${spacingTop}px`, height: '14px' }"
      @pointerdown.prevent.stop="startPaddingDrag('top', $event)"
      @click.stop
    >
      <div class="w-12 h-2 rounded-full bg-violet-500 opacity-75 group-hover/pad:opacity-100 transition-opacity shadow-sm" />
    </div>
    <!-- Bottom padding -->
    <div
      v-if="selected"
      class="absolute inset-x-8 z-30 flex items-center justify-center cursor-ns-resize group/pad"
      :style="{ bottom: `${spacingBottom}px`, height: '14px' }"
      @pointerdown.prevent.stop="startPaddingDrag('bottom', $event)"
      @click.stop
    >
      <div class="w-12 h-2 rounded-full bg-violet-500 opacity-75 group-hover/pad:opacity-100 transition-opacity shadow-sm" />
    </div>
    <!-- Left padding -->
    <div
      v-if="selected"
      class="absolute z-30 flex items-center justify-center cursor-ew-resize group/pad"
      :style="{ top: `${spacingTop}px`, bottom: `${spacingBottom}px`, left: 0, width: '14px' }"
      @pointerdown.prevent.stop="startPaddingDragH('left', $event)"
      @click.stop
    >
      <div class="w-2 h-12 rounded-full bg-violet-500 opacity-75 group-hover/pad:opacity-100 transition-opacity shadow-sm" />
    </div>
    <!-- Right padding -->
    <div
      v-if="selected"
      class="absolute z-30 flex items-center justify-center cursor-ew-resize group/pad"
      :style="{ top: `${spacingTop}px`, bottom: `${spacingBottom}px`, right: 0, width: '14px' }"
      @pointerdown.prevent.stop="startPaddingDragH('right', $event)"
      @click.stop
    >
      <div class="w-2 h-12 rounded-full bg-violet-500 opacity-75 group-hover/pad:opacity-100 transition-opacity shadow-sm" />
    </div>

    <!-- ── Corner resize dot (bottom-right of content area) ─────────────── -->
    <div
      v-if="selected && isTopLevel"
      title="Drag to resize"
      class="absolute w-3 h-3 rounded-full bg-white border-2 border-blue-500
             cursor-se-resize select-none z-40 shadow-sm hover:scale-125 transition-transform"
      :style="{ bottom: `${spacingBottom - 6}px`, right: '-6px' }"
      @pointerdown.prevent.stop="startCornerDrag($event)"
      @click.stop
    />

    <!-- ── Tooltip ────────────────────────────────────────────────────────── -->
    <Transition
      enter-active-class="transition-opacity duration-100"
      leave-active-class="transition-opacity duration-100"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div
        v-if="paddingTip"
        class="absolute right-1 text-xs bg-surface-gray-7 text-ink-white px-1.5 py-0.5 rounded pointer-events-none z-40 font-mono"
        :style="{ top: `${spacingTop + 4}px` }"
      >{{ paddingTip }}</div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useEditorStore } from "../stores/editor";

const props  = defineProps({ block: Object, index: Number, extraStyle: { type: Object, default: () => ({}) } });
const store  = useEditorStore();
const selected  = computed(() => store.selectedBlockId === props.block.id);
const isHovered = ref(false);

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

const contentClipStyle = computed(() => {
  const r = props.block.props?.block_border_radius;
  if (!r || r === "0") return {};
  return { overflow: "hidden", borderRadius: r };
});

// ── Top-level container width + alignment ────────────────────────────────────
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

// ── Block size ────────────────────────────────────────────────────────────────
const blockSizeStyle = computed(() => {
  if (['container', 'image'].includes(props.block.type) || !isTopLevel.value) return {};
  const w = props.block.props?.block_width;
  const h = props.block.props?.block_height;
  return {
    ...(w && w !== "auto" && w !== "" ? { width: w } : {}),
    ...(h && h !== "auto" && h !== "" ? { minHeight: h } : {}),
  };
});

// ── Spacing ───────────────────────────────────────────────────────────────────
const spacingTop    = computed(() => Number(props.block.props?.spacing_top    ?? 0));
const spacingBottom = computed(() => Number(props.block.props?.spacing_bottom ?? 0));

const spacingStyle = computed(() => {
  const t  = spacingTop.value;
  const b  = spacingBottom.value;
  const bg = props.block.props?.background_color;
  const hasBg = bg && bg !== "transparent";
  return {
    paddingTop:      t > 0 ? `${t}px` : undefined,
    paddingBottom:   b > 0 ? `${b}px` : undefined,
    backgroundColor: (t > 0 || b > 0) && hasBg ? bg : undefined,
  };
});

// ── Tip ──────────────────────────────────────────────────────────────────────
const paddingTip = ref(null);
let _tipTimer = null;

function showTip(msg) {
  paddingTip.value = msg;
  clearTimeout(_tipTimer);
  _tipTimer = setTimeout(() => (paddingTip.value = null), 1200);
}

// ── Padding resize ────────────────────────────────────────────────────────────
const DEFAULT_PADDING = { top: 20, right: 16, bottom: 20, left: 16 };

function startPaddingDrag(edge, e) {
  store.selectBlock(props.block.id);
  e.target.setPointerCapture(e.pointerId);
  const propKey  = `padding_${edge}`;
  const startY   = e.clientY;
  const startVal = parseInt(props.block.props[propKey] ?? DEFAULT_PADDING[edge]);
  store.updateBlockProps(props.block.id, { [propKey]: startVal });

  function onMove(ev) {
    const delta   = ev.clientY - startY;
    const clamped = Math.max(0, Math.round((startVal + delta) / 4) * 4);
    store.updateBlockPropsLive(props.block.id, { [propKey]: clamped });
    showTip(`${edge === 'top' ? '↑' : '↓'} pad ${clamped}px`);
  }
  function onUp() {
    e.target.removeEventListener("pointermove", onMove);
    e.target.removeEventListener("pointerup",   onUp);
  }
  e.target.addEventListener("pointermove", onMove);
  e.target.addEventListener("pointerup",   onUp);
}

function startPaddingDragH(edge, e) {
  store.selectBlock(props.block.id);
  e.target.setPointerCapture(e.pointerId);
  const propKey  = `padding_${edge}`;
  const startX   = e.clientX;
  const startVal = parseInt(props.block.props[propKey] ?? DEFAULT_PADDING[edge]);
  store.updateBlockProps(props.block.id, { [propKey]: startVal });

  function onMove(ev) {
    const delta   = ev.clientX - startX;
    const sign    = edge === "left" ? 1 : -1;
    const clamped = Math.max(0, Math.round((startVal + sign * delta) / 4) * 4);
    store.updateBlockPropsLive(props.block.id, { [propKey]: clamped });
    showTip(`${edge === 'left' ? '←' : '→'} pad ${clamped}px`);
  }
  function onUp() {
    e.target.removeEventListener("pointermove", onMove);
    e.target.removeEventListener("pointerup",   onUp);
  }
  e.target.addEventListener("pointermove", onMove);
  e.target.addEventListener("pointerup",   onUp);
}

// ── Spacing drag ──────────────────────────────────────────────────────────────
function startSpacingDrag(edge, e) {
  store.selectBlock(props.block.id);
  e.target.setPointerCapture(e.pointerId);
  const propKey  = `spacing_${edge}`;
  const startY   = e.clientY;
  const startVal = Number(props.block.props[propKey] ?? 0);
  store.updateBlockProps(props.block.id, { [propKey]: startVal });

  function onMove(ev) {
    const delta   = ev.clientY - startY;
    const clamped = Math.max(0, Math.round((startVal + delta) / 4) * 4);
    store.updateBlockPropsLive(props.block.id, { [propKey]: clamped });
    showTip(`spacing ${edge === "top" ? "↑" : "↓"} ${clamped}px`);
  }
  function onUp() {
    e.target.removeEventListener("pointermove", onMove);
    e.target.removeEventListener("pointerup",   onUp);
  }
  e.target.addEventListener("pointermove", onMove);
  e.target.addEventListener("pointerup",   onUp);
}

// ── Corner resize ─────────────────────────────────────────────────────────────
function startCornerDrag(e) {
  store.selectBlock(props.block.id);
  e.target.setPointerCapture(e.pointerId);

  const blockEl = e.currentTarget.parentElement;
  const startX  = e.clientX;
  const startY  = e.clientY;
  const startW  = blockEl ? blockEl.offsetWidth : 200;
  const startH  = blockEl ? (blockEl.offsetHeight - spacingTop.value - spacingBottom.value) : 100;

  const wKey = props.block.type === "container" ? "width"
             : props.block.type === "image"     ? "image_width"
             : "block_width";
  const hKey = props.block.type === "container" || props.block.type === "spacer" ? "height"
             : props.block.type === "image"     ? "image_height"
             : "block_height";

  const snapH = props.block.type === "spacer" ? startH : `${startH}px`;
  store.updateBlockProps(props.block.id, { [wKey]: `${startW}px`, [hKey]: snapH });

  function onMove(ev) {
    const dx   = ev.clientX - startX;
    const dy   = ev.clientY - startY;
    const newW = Math.max(60, Math.min(store.emailWidth, Math.round(startW + dx)));
    const newH = Math.max(8, Math.round(startH + dy));
    const hVal = props.block.type === "spacer" ? newH : `${newH}px`;
    store.updateBlockPropsLive(props.block.id, { [wKey]: `${newW}px`, [hKey]: hVal });
    showTip(`${newW} × ${newH}px`);
  }
  function onUp() {
    e.target.removeEventListener("pointermove", onMove);
    e.target.removeEventListener("pointerup",   onUp);
  }
  e.target.addEventListener("pointermove", onMove);
  e.target.addEventListener("pointerup",   onUp);
}
</script>
