<template>
  <BlockWrapper :block="block" :index="index">
    <div class="px-8 py-4">
      <hr
        :style="{
          borderColor: block.props.border_color,
          borderTopWidth: block.props.thickness + 'px',
          borderTopStyle: block.props.style,
        }"
        class="border-0"
      />
      <div class="flex gap-3 mt-3" @click.stop>
        <div class="flex items-center gap-1.5">
          <span class="text-xs text-gray-400">Color</span>
          <input type="color" :value="block.props.border_color" @input="update('border_color', $event.target.value)" class="w-7 h-7 rounded cursor-pointer border border-gray-300" />
        </div>
        <FormControl
          type="select"
          label="Thickness"
          size="sm"
          :options="[{label:'1px',value:1},{label:'2px',value:2},{label:'4px',value:4}]"
          :value="block.props.thickness"
          @change="update('thickness', Number($event.target.value))"
        />
        <FormControl
          type="select"
          label="Style"
          size="sm"
          :options="[{label:'Solid',value:'solid'},{label:'Dashed',value:'dashed'},{label:'Dotted',value:'dotted'}]"
          :value="block.props.style"
          @change="update('style', $event.target.value)"
        />
      </div>
    </div>
  </BlockWrapper>
</template>

<script setup>
import BlockWrapper from "../BlockWrapper.vue";
import { FormControl } from "frappe-ui";
import { useEditorStore } from "../../stores/editor";
const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();
function update(key, val) { store.updateBlockProps(props.block.id, { [key]: val }); }
</script>
