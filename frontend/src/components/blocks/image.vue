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

// Apply fixed height + object-fit directly on the img so no % chain needed.
// "contain" (icons/logos) shrink-wraps the img to its own aspect ratio at the
// fixed height ("auto" width) — the box was already left/right-aligned
// correctly, but width:"100%" stretched the <img> itself to fill the box
// regardless of the logo's real size, so a small square icon ended up
// visually centered inside an oversized box. "cover" is the opposite case:
// the whole point is to crop the image to fill a box the author explicitly
// sized via image_width (imageBoxStyle below), so the img must stay
// width:"100%" of that box — forcing "auto" there let the img render at its
// natural aspect ratio instead of the configured width, overflowing the
// clipped wrapper and showing only a cropped slice of the photo.
const imgStyle = computed(() => {
  const fit = props.block.props.image_fit || "cover";
  const h = props.block.props.image_height;
  const hasHeight = h && h !== "auto" && h !== "";
  const objPos = props.block.props.object_position || "center";
  return {
    display: "block",
    ...(hasHeight && fit === "contain"
      ? { width: "auto", height: h, objectFit: fit, objectPosition: objPos }
      : hasHeight
      ? { width: "100%", height: h, objectFit: fit, objectPosition: objPos }
      : { width: "100%" }),
  };
});
</script>
