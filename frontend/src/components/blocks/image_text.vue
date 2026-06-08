<template>
  <BlockWrapper :block="block" :index="index">
    <div
      class="flex gap-5 px-8 py-5 items-center"
      :class="{ 'flex-row-reverse': block.props.image_position === 'right' }"
      :style="{ backgroundColor: block.props.background_color }"
    >
      <!-- Image -->
      <div class="flex-shrink-0" :style="{ width: imageWidth }">
        <ImageUploader
          :url="block.props.image_url"
          height-class="h-32"
          replace-class="w-full text-center py-0.5"
          @uploaded="update('image_url', $event)"
        >
          <template #default="{ url }">
            <img :src="url" class="w-full rounded object-cover" />
          </template>
        </ImageUploader>
      </div>

      <!-- Text -->
      <div class="flex-1">
        <div
          class="outline-none min-h-10 leading-relaxed text-gray-700"
          contenteditable="true"
          @blur="update('text', $event.target.innerText)"
          @click.stop="store.selectBlock(block.id)"
        >{{ block.props.text }}</div>
      </div>
    </div>
  </BlockWrapper>
</template>

<script setup>
import { computed } from "vue";
import BlockWrapper from "../BlockWrapper.vue";
import ImageUploader from "../ImageUploader.vue";
import { useEditorStore } from "../../stores/editor";

const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();
function update(key, val) { store.updateBlockProps(props.block.id, { [key]: val }); }

// Image width from prop (e.g. "33%", "50%", "175px")
const imageWidth = computed(() => props.block.props.image_width || "175px");
</script>
