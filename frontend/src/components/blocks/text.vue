<template>
  <BlockWrapper :block="block" :index="index">
    <div class="px-8 py-5">
      <div
        class="outline-none min-h-10 leading-relaxed text-gray-700"
        :style="{ textAlign: block.props.align, fontSize: block.props.font_size }"
        contenteditable="true"
        @blur="update('content', $event.target.innerText)"
        @click.stop
      >{{ block.props.content }}</div>
      <div class="flex gap-3 mt-3" @click.stop>
        <FormControl
          type="select"
          label="Align"
          size="sm"
          :options="[{label:'Left',value:'left'},{label:'Center',value:'center'},{label:'Right',value:'right'}]"
          :value="block.props.align"
          @change="update('align', $event.target.value)"
        />
        <FormControl
          type="select"
          label="Size"
          size="sm"
          :options="[{label:'Small',value:'14px'},{label:'Normal',value:'16px'},{label:'Large',value:'20px'}]"
          :value="block.props.font_size"
          @change="update('font_size', $event.target.value)"
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
