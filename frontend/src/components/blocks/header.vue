<template>
  <BlockWrapper :block="block" :index="index">
    <div
      :style="{
        backgroundColor: block.props.background_color || '#ffffff',
        borderBottom: block.props.border_bottom !== false ? '1px solid #e5e7eb' : 'none',
        ...paddingStyle,
      }"
      class="flex flex-col"
      :class="{
        'items-center': block.props.align === 'center' || !block.props.align,
        'items-start':  block.props.align === 'left',
        'items-end':    block.props.align === 'right',
      }"
    >
      <!-- Logo image -->
      <ImageUploader
        :url="block.props.logo_url"
        :alt="'Logo'"
        height-class="h-10"
        @uploaded="update('logo_url', $event)"
      >
        <template #default="{ url }">
          <img
            v-if="url"
            :src="url"
            alt="Logo"
            :style="{ height: block.props.logo_height || '40px', width: 'auto', display: 'block' }"
          />
          <div
            v-else
            class="flex items-center justify-center bg-gray-100 rounded text-gray-400 text-xs"
            :style="{ height: block.props.logo_height || '40px', width: '120px' }"
          >Logo</div>
        </template>
      </ImageUploader>

      <!-- Optional tagline -->
      <EditableDiv
        v-if="block.props.tagline !== undefined"
        class="mt-2 text-sm outline-none"
        :style="{ color: block.props.tagline_color || '#6b7280' }"
        :model-value="block.props.tagline || ''"
        placeholder="Issue tagline..."
        @update:model-value="update('tagline', $event)"
        @click.stop="store.selectBlock(block.id)"
      />
    </div>
  </BlockWrapper>
</template>

<script setup>
import { computed } from "vue";
import BlockWrapper from "../BlockWrapper.vue";
import ImageUploader from "../ImageUploader.vue";
import EditableDiv from "../EditableDiv.vue";
import { useEditorStore } from "../../stores/editor";
import { usePadding } from "../../composables/usePadding";

const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();
function update(key, val) { store.updateBlockProps(props.block.id, { [key]: val }); }

const blockProps = computed(() => props.block.props);
const paddingStyle = usePadding(blockProps, { top: 20, right: 32, bottom: 20, left: 32 });
</script>
