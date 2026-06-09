<template>
  <BlockWrapper :block="block" :index="index">
    <div :style="{ backgroundColor: block.props.background_color, ...paddingStyle }">

      <ImageUploader
        :url="block.props.image_url"
        :alt="block.props.alt || ''"
        height-class="h-44"
        @uploaded="update('image_url', $event)"
      >
        <!-- Wrap in a div so border-radius + overflow:hidden clips the image correctly -->
        <template #default="{ url }">
          <div
            :style="{
              borderRadius: block.props.border_radius || '0',
              overflow: 'hidden',
              border: block.props.border && block.props.border !== 'none'
                ? block.props.border : 'none',
              display: 'block',
              lineHeight: 0,
            }"
          >
            <img
              :src="url"
              :alt="block.props.alt || ''"
              class="w-full block"
            />
          </div>
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
import { computed } from "vue";
import BlockWrapper from "../BlockWrapper.vue";
import ImageUploader from "../ImageUploader.vue";
import { useEditorStore } from "../../stores/editor";
import { usePadding } from "../../composables/usePadding";

const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();
function update(key, val) { store.updateBlockProps(props.block.id, { [key]: val }); }

const blockProps = computed(() => props.block.props);
const paddingStyle = usePadding(blockProps, { top: 16, right: 32, bottom: 16, left: 32 });
</script>
