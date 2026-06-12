<template>
  <BlockWrapper :block="block" :index="index">
    <div :style="paddingStyle" class="flex" :class="alignClass">
      <div
        :style="{
          width: block.props.width || '100%',
          height: block.props.thickness + 'px',
          backgroundColor: block.props.style === 'solid' ? block.props.border_color : 'transparent',
          borderTop: block.props.style !== 'solid'
            ? `${block.props.thickness}px ${block.props.style} ${block.props.border_color}`
            : 'none',
        }"
      />
    </div>
  </BlockWrapper>
</template>

<script setup>
import { computed } from "vue";
import BlockWrapper from "../BlockWrapper.vue";
import { usePadding } from "../../composables/usePadding";
const props = defineProps({ block: Object, index: Number });

const blockProps = computed(() => props.block.props);
const paddingStyle = usePadding(blockProps, { top: 16, right: 16, bottom: 16, left: 16 });

const alignClass = computed(() => {
  const a = props.block.props.align || "center";
  return a === "left" ? "justify-start" : a === "right" ? "justify-end" : "justify-center";
});
</script>
