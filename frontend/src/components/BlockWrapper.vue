<template>
  <div
    class="relative rounded border-2 transition-colors cursor-pointer"
    :class="selected
      ? 'border-gray-900 shadow-sm'
      : 'border-transparent hover:border-gray-200'"
    :style="spacingStyle"
    @click.stop="store.selectBlock(block.id)"
  >
    <slot />
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useEditorStore } from "../stores/editor";

const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();
const selected = computed(() => store.selectedBlockId === props.block.id);

const spacingStyle = computed(() => {
  const t = props.block.props?.spacing_top;
  const b = props.block.props?.spacing_bottom;
  return {
    marginTop:    t != null ? `${t}px` : "4px",
    marginBottom: b != null ? `${b}px` : "4px",
  };
});
</script>
