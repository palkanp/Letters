<template>
  <!-- width/minHeight live here so they apply to the full wrapper, not double-counted -->
  <BlockWrapper :block="block" :index="index" :extra-style="wrapperStyle">
    <div
      :style="{
        backgroundColor: block.props.background_color || undefined,
        display: 'flex',
        flexDirection: block.props.layout === 'row' ? 'row' : 'column',
        alignItems:     block.props.layout === 'row' ? (block.props.vertical_align || 'stretch') : undefined,
        justifyContent: block.props.layout !== 'row' ? (block.props.vertical_align || 'flex-start') : undefined,
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
          class="relative rounded"
          :style="childFlexStyle(child)"
          @click.stop="store.selectBlock(child.id)"
        >
          <!-- Render the child block -->
          <BlockRenderer :block="child" :index="childIndex" />
        </div>
      </template>

      <!-- Empty state -->
      <div
        v-else
        class="flex items-center justify-center py-6 select-none"
      >
        <Button
          variant="ghost"
          icon="lucide-plus"
          size="sm"
          title="Add block inside"
          class="!w-7 !h-7"
          @click.stop="openPicker({ mode: 'child', parentId: block.id, afterIndex: -1 })"
        />
      </div>
    </div>
  </BlockWrapper>
</template>

<script setup>
import { computed, inject } from "vue";
import BlockWrapper from "../BlockWrapper.vue";
import BlockRenderer from "../BlockRenderer.vue";
import { useEditorStore } from "../../stores/editor";
import { usePadding } from "../../composables/usePadding";

const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();
const openPicker = inject("openPicker", () => {});

const blockProps = computed(() => props.block.props);
const paddingStyle = usePadding(blockProps, { top: 16, right: 16, bottom: 16, left: 16 });

const wrapperStyle = computed(() => {
  const h  = props.block.props.height;
  const bg = props.block.props.background_color;
  return {
    ...(h && h !== "auto" && h !== "0px" ? { minHeight: h } : {}),
    ...(bg && bg !== "transparent" ? { backgroundColor: bg } : {}),
  };
});

function childFlexStyle(child) {
  const bw = child.props?.block_width;
  const bh = child.props?.block_height;
  const heightStyle = bh && bh !== "auto" ? { minHeight: bh } : {};

  if (props.block.props.layout === "row") {
    if (bw && bw !== "auto") return { flex: `0 0 ${bw}`, minWidth: 0, alignSelf: "stretch", ...heightStyle };
    const fw = child.props?.flex_width;
    if (fw && fw !== "auto") return { flex: `0 0 ${fw}`, minWidth: 0, alignSelf: "stretch", ...heightStyle };
    if (fw === "auto")       return { flex: "0 0 auto",  minWidth: 0, alignSelf: "stretch", ...heightStyle };
    if (child.type === "divider" && child.props?.orientation === "vertical") {
      return { flex: "0 0 auto", minWidth: 0, alignSelf: "stretch", ...heightStyle };
    }
    const w = child.props?.width;
    const hasWidth = w && w !== "auto" && w !== "100%" && w !== "0px";
    if (hasWidth) return { flex: `0 0 ${w}`, minWidth: 0, alignSelf: alignSelfMap[child.props?.align] || "stretch", ...heightStyle };
    return { flex: "1 1 0", minWidth: 0, ...heightStyle };
  } else {
    const w = bw || child.props?.width;
    const hasWidth = w && w !== "auto" && w !== "100%" && w !== "0px";
    if (hasWidth) return { width: w, alignSelf: alignSelfMap[child.props?.align] || "stretch", ...heightStyle };
    return { ...heightStyle };
  }
}

const alignSelfMap = { left: "flex-start", center: "center", right: "flex-end" };

</script>
