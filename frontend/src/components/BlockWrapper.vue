<template>
  <div
    class="relative rounded border-2 my-1 cursor-pointer transition-colors"
    :class="selected ? 'border-blue-500' : 'border-transparent hover:border-gray-300'"
    @click.stop="selected = true"
  >
    <!-- Toolbar -->
    <div
      v-if="selected"
      class="absolute -top-8 right-0 z-10 flex items-center gap-1 bg-gray-900 rounded px-2 py-1"
    >
      <span class="text-xs text-gray-400 capitalize px-1">{{ block.type.replace('_', ' ') }}</span>
      <Button
        variant="ghost"
        size="sm"
        :disabled="index === 0"
        class="!text-gray-300 !h-5 !w-5 !p-0 text-xs"
        @click.stop="store.moveBlock(index, index - 1)"
      >↑</Button>
      <Button
        variant="ghost"
        size="sm"
        :disabled="index === store.blocks.length - 1"
        class="!text-gray-300 !h-5 !w-5 !p-0 text-xs"
        @click.stop="store.moveBlock(index, index + 1)"
      >↓</Button>
      <Button
        variant="ghost"
        size="sm"
        class="!text-red-400 !h-5 !w-5 !p-0 text-xs"
        @click.stop="store.removeBlock(block.id)"
      >✕</Button>
    </div>

    <slot />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { Button } from "frappe-ui";
import { useEditorStore } from "../stores/editor";

const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();
const selected = ref(false);

function handleOutsideClick() {
  selected.value = false;
}

onMounted(() => document.addEventListener("click", handleOutsideClick));
onUnmounted(() => document.removeEventListener("click", handleOutsideClick));
</script>
