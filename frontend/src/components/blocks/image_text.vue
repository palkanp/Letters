<template>
  <BlockWrapper :block="block" :index="index">
    <div
      class="flex gap-5 px-8 py-5 items-center"
      :class="{ 'flex-row-reverse': block.props.image_position === 'right' }"
    >
      <!-- Image slot -->
      <div class="flex-shrink-0 w-44" @click.stop>
        <img v-if="block.props.image_url" :src="block.props.image_url" class="w-full rounded" />
        <div
          v-else
          class="w-full h-28 border-2 border-dashed border-gray-300 rounded flex flex-col items-center justify-center gap-2 bg-gray-50"
        >
          <span class="text-xs text-gray-400">Image</span>
          <TextInput
            size="sm"
            placeholder="Paste URL…"
            :value="block.props.image_url"
            @change="update('image_url', $event.target.value)"
            class="w-36"
          />
        </div>
      </div>

      <!-- Text + controls -->
      <div class="flex-1">
        <div
          class="outline-none min-h-10 leading-relaxed text-gray-700"
          contenteditable="true"
          @blur="update('text', $event.target.innerText)"
          @click.stop
        >{{ block.props.text }}</div>
        <div class="flex gap-3 mt-3 flex-wrap" @click.stop>
          <FormControl
            type="select"
            label="Image side"
            size="sm"
            :options="[{label:'Left',value:'left'},{label:'Right',value:'right'}]"
            :value="block.props.image_position"
            @change="update('image_position', $event.target.value)"
          />
          <div v-if="block.props.image_url">
            <TextInput
              size="sm"
              :value="block.props.image_url"
              @change="update('image_url', $event.target.value)"
              placeholder="Image URL"
              class="w-48"
            />
          </div>
        </div>
      </div>
    </div>
  </BlockWrapper>
</template>

<script setup>
import BlockWrapper from "../BlockWrapper.vue";
import { TextInput } from "frappe-ui";
import { FormControl } from "frappe-ui";
import { useEditorStore } from "../../stores/editor";
const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();
function update(key, val) { store.updateBlockProps(props.block.id, { [key]: val }); }
</script>
