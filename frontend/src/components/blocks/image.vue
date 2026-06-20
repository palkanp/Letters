<template>
  <BlockWrapper :block="block" :index="index">
    <div :style="{ backgroundColor: block.props.background_color, ...paddingStyle, ...alignWrapStyle }">

      <!-- Sized wrapper — controls image_width; alignment is on the outer flex div -->
      <div :style="imageBoxStyle">
        <ImageUploader
          :url="block.props.image_url"
          :alt="block.props.alt || ''"
          :height-class="block.props.height_class || 'h-44'"
          :compact="!!block.props.compact"
          @uploaded="update('image_url', $event)"
        >
          <template #default="{ url }">
            <div :style="innerWrapStyle">
              <img
                :src="url"
                :alt="block.props.alt || ''"
                :style="imgStyle"
              />
            </div>
          </template>
        </ImageUploader>
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
const paddingStyle = usePadding(blockProps, { top: 16, right: 16, bottom: 16, left: 16 });

const alignJustify = { left: "flex-start", center: "center", right: "flex-end" };

// Outer padding div is a flex row so image_align repositions the image box
const alignWrapStyle = computed(() => ({
  display: "flex",
  justifyContent: alignJustify[props.block.props.image_align || "center"] || "center",
}));

// Constrains the ImageUploader to image_width (default 100%)
const imageBoxStyle = computed(() => ({
  width: props.block.props.image_width || "100%",
}));

// Border-radius + overflow to clip image corners
const innerWrapStyle = computed(() => ({
  borderRadius: props.block.props.border_radius || "0",
  overflow: "hidden",
  border: props.block.props.border && props.block.props.border !== "none"
    ? props.block.props.border : "none",
  lineHeight: 0,
}));

// Apply fixed height + object-fit directly on the img so no % chain needed
const imgStyle = computed(() => {
  const fit = props.block.props.image_fit || "cover";
  const h = props.block.props.image_height;
  const hasHeight = h && h !== "auto" && h !== "";
  return {
    width: "100%",
    display: "block",
    ...(hasHeight ? { height: h, objectFit: fit } : {}),
  };
});
</script>
