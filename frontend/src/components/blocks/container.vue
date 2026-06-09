<template>
  <!-- width/minHeight live here so they apply to the full wrapper, not double-counted -->
  <BlockWrapper :block="block" :index="index" :extra-style="wrapperStyle">
    <div
      :style="{
        backgroundColor: block.props.background_color || '#f8fafc',
        border: `1px solid ${block.props.border_color || '#e2e8f0'}`,
        borderRadius: block.props.border_radius || '12px',
        display: 'flex',
        flexDirection: block.props.layout === 'row' ? 'row' : 'column',
        gap: `${block.props.gap ?? 12}px`,
        height: '100%',
        ...paddingStyle,
      }"
    >
      <!-- Children -->
      <template v-if="block.children?.length">
        <div
          v-for="(child, childIndex) in block.children"
          :key="child.id"
          class="relative group/child rounded transition-colors"
          :class="childDragOver === childIndex ? 'ring-2 ring-blue-400' : ''"
          :style="childFlexStyle(child)"
          draggable="true"
          @click.stop="store.selectBlock(child.id)"
          @dragstart.stop="onChildDragStart(childIndex, $event)"
          @dragover.stop.prevent="onChildDragOver(childIndex, $event)"
          @dragleave.stop="childDragOver = null"
          @drop.stop.prevent="onChildDrop(childIndex)"
          @dragend.stop="childDragFrom = null; childDragOver = null"
        >
          <!-- Drop indicator -->
          <div v-if="childDragOver === childIndex && childDragFrom !== null && childDragFrom !== childIndex"
            class="absolute inset-x-0 -top-px h-0.5 bg-blue-500 rounded-full pointer-events-none z-20" />
          <!-- Selection ring -->
          <div
            class="absolute inset-0 rounded pointer-events-none z-10 transition-all"
            :class="store.selectedBlockId === child.id
              ? 'ring-2 ring-blue-400 ring-offset-1'
              : 'group-hover/child:ring-1 group-hover/child:ring-blue-200'"
          />
          <!-- Drag grip -->
          <div
            class="absolute top-1/2 -translate-y-1/2 -left-5 w-4 h-6 flex items-center justify-center
                   cursor-grab active:cursor-grabbing select-none rounded
                   text-gray-300 hover:text-gray-500 hover:bg-gray-100 transition-all z-20
                   opacity-0 group-hover/child:opacity-100"
            @click.stop
          >
            <svg width="8" height="12" viewBox="0 0 8 12" fill="currentColor">
              <circle cx="2" cy="2"  r="1.2"/><circle cx="6" cy="2"  r="1.2"/>
              <circle cx="2" cy="6"  r="1.2"/><circle cx="6" cy="6"  r="1.2"/>
              <circle cx="2" cy="10" r="1.2"/><circle cx="6" cy="10" r="1.2"/>
            </svg>
          </div>
          <!-- Remove child button -->
          <button
            type="button"
            class="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-white border border-gray-200
                   shadow-sm text-gray-400 hover:text-red-500 hover:border-red-200
                   text-xs leading-none z-20
                   opacity-0 group-hover/child:opacity-100 transition-opacity
                   flex items-center justify-center"
            title="Remove block"
            @click.stop="store.removeBlock(child.id)"
          >✕</button>
          <!-- Render the child block -->
          <BlockRenderer :block="child" :index="childIndex" />
        </div>
      </template>

      <!-- Empty state -->
      <div
        v-else
        class="flex flex-col items-center justify-center gap-2 py-8 select-none pointer-events-none"
      >
        <div class="text-2xl opacity-20">⬚</div>
        <p class="text-xs text-gray-400 text-center leading-relaxed">
          Empty — use the <strong>Layers</strong> panel<br/>
          <span class="text-gray-300">to add blocks inside</span>
        </p>
      </div>
    </div>
  </BlockWrapper>
</template>

<script setup>
import { computed, ref } from "vue";
import BlockWrapper from "../BlockWrapper.vue";
import BlockRenderer from "../BlockRenderer.vue";
import { useEditorStore } from "../../stores/editor";
import { usePadding } from "../../composables/usePadding";

const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();

const blockProps = computed(() => props.block.props);
const paddingStyle = usePadding(blockProps, { top: 16, right: 16, bottom: 16, left: 16 });

// width + minHeight go on the BlockWrapper so they aren't applied twice
// (the parent's childFlexStyle also reads width, so the inner div must NOT repeat it)
// Width is NOT set here — it's applied by the parent's childFlexStyle on the
// child-wrapper div. Setting it here too would cause double-application (% of %).
// Only minHeight lives here since it doesn't affect the parent's sizing.
const wrapperStyle = computed(() => {
  const h = props.block.props.height;
  return {
    ...(h && h !== "auto" && h !== "0px" ? { minHeight: h } : {}),
  };
});

// ── Child sizing (row flex + column width) ───────────────────────────────────
// Width is always applied HERE on the child-wrapper div, never on BlockWrapper,
// to avoid double-application (% of % bug).
function childFlexStyle(child) {
  const w = child.props?.width;
  const hasWidth = w && w !== "auto" && w !== "100%" && w !== "0px";
  if (props.block.props.layout === "row") {
    if (hasWidth) return { flex: `0 0 ${w}`, minWidth: 0, alignSelf: alignSelfMap[child.props?.align] || "stretch" };
    return { flex: "1 1 0", minWidth: 0 };
  } else {
    // column layout: explicit width shrinks the block; default fills container
    if (hasWidth) return { width: w, alignSelf: alignSelfMap[child.props?.align] || "stretch" };
    return {};
  }
}

const alignSelfMap = { left: "flex-start", center: "center", right: "flex-end" };

// ── Child drag-to-reorder ────────────────────────────────────────────────────
const childDragFrom = ref(null);
const childDragOver = ref(null);

function onChildDragStart(index, e) {
  childDragFrom.value = index;
  e.dataTransfer.effectAllowed = "move";
}
function onChildDragOver(index) {
  if (childDragFrom.value === null) return;
  childDragOver.value = index;
}
function onChildDrop(toIndex) {
  const from = childDragFrom.value;
  childDragFrom.value = null;
  childDragOver.value = null;
  if (from === null || from === toIndex) return;
  store.moveChildBlock(props.block.id, from, toIndex);
}
</script>
