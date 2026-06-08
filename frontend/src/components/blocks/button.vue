<template>
  <BlockWrapper :block="block" :index="index">
    <div class="px-8 py-5">
      <div :class="alignClass">
        <span
          class="inline-block rounded px-6 py-2.5 font-semibold cursor-text outline-none"
          :style="{ backgroundColor: block.props.color, color: block.props.text_color }"
          contenteditable="true"
          @blur="update('label', $event.target.innerText)"
          @click.stop
        >{{ block.props.label }}</span>
      </div>
      <div class="flex gap-3 mt-3 flex-wrap" @click.stop>
        <TextInput
          size="sm"
          :value="block.props.url"
          @change="update('url', $event.target.value)"
          placeholder="https://…"
          class="w-44"
        />
        <div class="flex items-center gap-1.5">
          <span class="text-xs text-gray-400">BG</span>
          <input type="color" :value="block.props.color" @input="update('color', $event.target.value)" class="w-7 h-7 rounded cursor-pointer border border-gray-300" />
        </div>
        <div class="flex items-center gap-1.5">
          <span class="text-xs text-gray-400">Text</span>
          <input type="color" :value="block.props.text_color" @input="update('text_color', $event.target.value)" class="w-7 h-7 rounded cursor-pointer border border-gray-300" />
        </div>
        <FormControl
          type="select"
          label="Align"
          size="sm"
          :options="[{label:'Left',value:'left'},{label:'Center',value:'center'},{label:'Right',value:'right'}]"
          :value="block.props.align"
          @change="update('align', $event.target.value)"
        />
      </div>
    </div>
  </BlockWrapper>
</template>

<script setup>
import BlockWrapper from "../BlockWrapper.vue";
import { TextInput } from "frappe-ui";
import { FormControl } from "frappe-ui";
import { computed } from "vue";
import { useEditorStore } from "../../stores/editor";
const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();
function update(key, val) { store.updateBlockProps(props.block.id, { [key]: val }); }
const alignClass = computed(() => ({
  'text-left': props.block.props.align === 'left',
  'text-center': props.block.props.align === 'center',
  'text-right': props.block.props.align === 'right',
}));
</script>
