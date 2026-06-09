<template>
  <BlockWrapper :block="block" :index="index">
    <div :style="paddingStyle">
      <a
        :href="block.props.video_url || '#'"
        target="_blank"
        class="block relative overflow-hidden no-underline group"
        :style="{ borderRadius: block.props.border_radius || '8px' }"
        @click.prevent="store.selectBlock(block.id)"
      >
        <!-- Thumbnail -->
        <ImageUploader
          :url="block.props.thumbnail_url"
          height-class="h-52"
          @uploaded="update('thumbnail_url', $event)"
        >
          <template #default="{ url }">
            <img
              v-if="url"
              :src="url"
              class="w-full object-cover block"
              style="height: 208px"
            />
            <div v-else class="w-full bg-gray-200 flex items-center justify-center text-gray-400 text-sm" style="height:208px;">
              Click to upload thumbnail
            </div>
          </template>
        </ImageUploader>

        <!-- Dark overlay -->
        <div
          class="absolute inset-0 flex items-center justify-center transition-opacity group-hover:opacity-80"
          :style="{ backgroundColor: block.props.overlay_color || 'rgba(0,0,0,0.3)', borderRadius: block.props.border_radius || '8px' }"
        >
          <!-- Play button circle -->
          <div
            class="w-16 h-16 rounded-full flex items-center justify-center shadow-lg"
            :style="{ backgroundColor: block.props.play_button_color || '#ffffff' }"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <polygon points="8,5 19,12 8,19" :fill="block.props.play_icon_color || '#111827'" />
            </svg>
          </div>
        </div>
      </a>

      <!-- Caption -->
      <div
        v-if="block.props.caption"
        class="mt-2 text-center text-xs text-gray-500 outline-none"
        contenteditable="true"
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
const paddingStyle = usePadding(blockProps);
</script>
