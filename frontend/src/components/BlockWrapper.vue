<template>
  <div
    class="relative rounded border-2 my-1 transition-colors cursor-pointer"
    :class="selected
      ? 'border-gray-900 shadow-sm'
      : 'border-transparent hover:border-gray-200'"
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
</script>
