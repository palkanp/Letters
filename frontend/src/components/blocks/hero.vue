<template>
  <BlockWrapper :block="block" :index="index">
    <div class="px-8 py-10 text-center" :style="{ backgroundColor: block.props.background_color }">
      <div
        class="text-3xl font-bold text-gray-900 outline-none mb-2"
        contenteditable="true"
        @blur="update('heading', $event.target.innerText)"
        @click.stop
      >{{ block.props.heading }}</div>
      <div
        class="text-base text-gray-500 outline-none mb-4"
        contenteditable="true"
        @blur="update('subheading', $event.target.innerText)"
        @click.stop
      >{{ block.props.subheading }}</div>
      <div class="flex justify-center items-center gap-2 mt-2" @click.stop>
        <span class="text-xs text-gray-400">Background</span>
        <input
          type="color"
          :value="block.props.background_color"
          @input="update('background_color', $event.target.value)"
          class="w-7 h-7 rounded cursor-pointer border border-gray-300"
        />
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
