<template>
  <BlockWrapper :block="block" :index="index">
    <div class="px-8 py-4" :style="{ backgroundColor: block.props.background_color }">

      <ImageUploader
        :url="block.props.image_url"
        :alt="block.props.alt || ''"
        height-class="h-44"
        @uploaded="update('image_url', $event)"
      >
        <!-- Custom framing: full-width with configurable border + radius -->
        <template #default="{ url }">
          <img
            :src="url"
            :alt="block.props.alt || ''"
            class="w-full block"
            :style="{
              border: block.props.border || 'none',
              borderRadius: block.props.border_radius || '0',
            }"
          />
        </template>
      </ImageUploader>

      <!-- Caption -->
      <div
        v-if="block.props.image_url || block.props.caption"
        class="mt-2 text-xs outline-none"
        :style="{ color: block.props.caption_color || '#9ca3af' }"
        contenteditable="true"
        data-placeholder="Add a caption…"
        @blur="update('caption', $event.target.innerText)"
        @click.stop="store.selectBlock(block.id)"
      >{{ block.props.caption }}</div>
    </div>
  </BlockWrapper>
</template>

<script setup>
import BlockWrapper from "../BlockWrapper.vue";
import ImageUploader from "../ImageUploader.vue";
import { useEditorStore } from "../../stores/editor";

const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();
function update(key, val) { store.updateBlockProps(props.block.id, { [key]: val }); }
</script>
