<template>
  <BlockWrapper :block="block" :index="index">
    <div
      class="px-8 py-5 text-center"
      :style="{ backgroundColor: block.props.background_color }"
    >
      <div
        class="text-xs leading-relaxed outline-none"
        :style="{ color: block.props.text_color }"
        contenteditable="true"
        @blur="update('text', $event.target.innerText)"
        @click.stop
      >{{ block.props.text }}</div>
      <div class="flex justify-center gap-3 mt-3" @click.stop>
        <div class="flex items-center gap-1.5">
          <span class="text-xs text-gray-400">BG</span>
          <input type="color" :value="block.props.background_color" @input="update('background_color', $event.target.value)" class="w-7 h-7 rounded cursor-pointer border border-gray-300" />
        </div>
        <div class="flex items-center gap-1.5">
          <span class="text-xs text-gray-400">Text</span>
          <input type="color" :value="block.props.text_color" @input="update('text_color', $event.target.value)" class="w-7 h-7 rounded cursor-pointer border border-gray-300" />
        </div>
      </div>
    </div>
  </BlockWrapper>
</template>

<script setup>
import BlockWrapper from "../BlockWrapper.vue";
import { useEditorStore } from "../../stores/editor";
const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();
function update(key, val) { store.updateBlockProps(props.block.id, { [key]: val }); }
</script>
