<template>
  <BlockWrapper :block="block" :index="index">
    <div :style="paddingStyle">
      <div
        :style="cardStyle"
        class="overflow-hidden"
      >
        <!-- Product image -->
        <ImageUploader
          :url="block.props.image_url"
          height-class="h-44"
          @uploaded="update('image_url', $event)"
        >
          <template #default="{ url }">
            <img
              v-if="url"
              :src="url"
              class="w-full object-cover block"
              style="height: 176px"
            />
            <div v-else class="w-full bg-gray-100 flex items-center justify-center text-gray-400 text-xs" style="height:176px;">
              Click to upload image
            </div>
          </template>
        </ImageUploader>

        <!-- Content -->
        <div class="p-4">
          <!-- Title -->
          <div
            class="font-semibold text-base leading-snug outline-none mb-1"
            :style="{ color: block.props.title_color }"
            contenteditable="true"
            @blur="update('title', $event.target.innerText)"
            @click.stop="store.selectBlock(block.id)"
          >{{ block.props.title }}</div>

          <!-- Description -->
          <div
            class="text-sm leading-relaxed outline-none mb-3"
            :style="{ color: block.props.text_color }"
            contenteditable="true"
            @blur="update('description', $event.target.innerText)"
            @click.stop="store.selectBlock(block.id)"
          >{{ block.props.description }}</div>

          <!-- Price + CTA row -->
          <div class="flex items-center justify-between gap-3">
            <div
              class="text-lg font-bold outline-none"
              :style="{ color: block.props.title_color }"
              contenteditable="true"
              @blur="update('price', $event.target.innerText)"
              @click.stop="store.selectBlock(block.id)"
            >{{ block.props.price }}</div>
            <a
              v-if="block.props.button_label"
              :href="block.props.button_url || '#'"
              class="inline-block px-4 py-2 rounded-lg text-xs font-semibold no-underline"
              :style="{ backgroundColor: block.props.button_color, color: '#ffffff' }"
              @click.prevent="store.selectBlock(block.id)"
            >{{ block.props.button_label }}</a>
          </div>
        </div>
      </div>
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

const cardStyle = computed(() => ({
  backgroundColor: props.block.props.background_color,
  border: `1px solid ${props.block.props.border_color}`,
  borderRadius: props.block.props.border_radius || "12px",
}));
</script>
