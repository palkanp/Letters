<template>
  <BlockWrapper :block="block" :index="index">
    <div
      :style="{ backgroundColor: block.props.background_color, ...paddingStyle }"
    >
      <!-- Wrap mode: image floats, text flows around it -->
      <template v-if="isWrapMode">
        <div :style="floatImageStyle" class="relative">
          <ImageUploader
            :url="block.props.image_url"
            height-class="h-32"
            @uploaded="update('image_url', $event)"
          >
            <template #default="{ url }">
              <img :src="url" class="w-full rounded object-cover block" />
            </template>
          </ImageUploader>
          <!-- Width resize handle -->
          <div
            v-if="store.selectedBlockId === block.id"
            title="Drag to resize image"
            class="absolute top-0 bottom-0 -right-1.5 w-3 flex items-center justify-center
                   cursor-ew-resize z-10 group"
            @pointerdown.prevent.stop="startImageResize($event)"
            @click.stop
          >
            <div class="w-1 h-8 rounded-full bg-ink-gray-4 group-hover:bg-ink-gray-7 transition-colors opacity-60 group-hover:opacity-100" />
          </div>
          <!-- Width tooltip -->
          <div
            v-if="resizeTip"
            class="absolute -top-6 left-1/2 -translate-x-1/2 text-xs bg-ink-gray-9 text-white
                   px-1.5 py-0.5 rounded pointer-events-none whitespace-nowrap font-mono z-20"
          >{{ resizeTip }}</div>
        </div>
        <EditableDiv
          class="outline-none leading-relaxed text-ink-gray-7"
          :style="{ fontFamily: fontStack(block.props.font_family, 'Arial, Helvetica, sans-serif') }"
          :model-value="block.props.text"
          @update:model-value="update('text', $event)"
          @click.stop="store.selectBlock(block.id)"
        />
        <!-- clearfix -->
        <div style="clear:both"></div>
      </template>

      <!-- Side-by-side mode (default) -->
      <template v-else>
        <div
          class="flex gap-5 items-center"
          :class="{ 'flex-row-reverse': block.props.image_position === 'right' }"
        >
          <!-- Image with resize handle -->
          <div class="relative flex-shrink-0" :style="{ width: imageWidth }">
            <ImageUploader
              :url="block.props.image_url"
              height-class="h-32"
              @uploaded="update('image_url', $event)"
            >
              <template #default="{ url }">
                <img :src="url" class="w-full rounded object-cover" />
              </template>
            </ImageUploader>

            <!-- Width resize handle -->
            <div
              v-if="store.selectedBlockId === block.id"
              title="Drag to resize image"
              class="absolute top-0 bottom-0 -right-1.5 w-3 flex items-center justify-center
                     cursor-ew-resize z-10 group"
              @pointerdown.prevent.stop="startImageResize($event)"
              @click.stop
            >
              <div class="w-1 h-8 rounded-full bg-ink-gray-4 group-hover:bg-ink-gray-7 transition-colors opacity-60 group-hover:opacity-100" />
            </div>

            <!-- Width tooltip -->
            <div
              v-if="resizeTip"
              class="absolute -top-6 left-1/2 -translate-x-1/2 text-xs bg-ink-gray-9 text-white
                     px-1.5 py-0.5 rounded pointer-events-none whitespace-nowrap font-mono z-20"
            >{{ resizeTip }}</div>
          </div>

          <!-- Text -->
          <div class="flex-1">
            <EditableDiv
              class="outline-none leading-relaxed text-ink-gray-7"
              :style="{ fontFamily: fontStack(block.props.font_family, 'Arial, Helvetica, sans-serif') }"
              :model-value="block.props.text"
              @update:model-value="update('text', $event)"
              @click.stop="store.selectBlock(block.id)"
            />
          </div>
        </div>
      </template>
    </div>
  </BlockWrapper>
</template>

<script setup>
import { ref, computed } from "vue";
import { fontStack } from "../../fonts";
import BlockWrapper from "../BlockWrapper.vue";
import ImageUploader from "../ImageUploader.vue";
import EditableDiv from "../EditableDiv.vue";
import { useEditorStore } from "../../stores/editor";
import { usePadding } from "../../composables/usePadding";

const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();
function update(key, val) { store.updateBlockProps(props.block.id, { [key]: val }); }

const blockProps = computed(() => props.block.props);
const paddingStyle = usePadding(blockProps);

const imageWidth    = computed(() => props.block.props.image_width || "160px");
const isWrapMode    = computed(() => props.block.props.layout_mode === "wrap");

// In wrap mode, the image floats left or right with a margin so text flows around it
const floatImageStyle = computed(() => {
  const side = props.block.props.image_position === "right" ? "right" : "left";
  const margin = side === "right"
    ? { marginLeft: "16px", marginRight: "0" }
    : { marginLeft: "0",    marginRight: "16px" };
  return {
    float: side,
    width: imageWidth.value,
    ...margin,
    marginBottom: "8px",
  };
});

// ── Image width drag resize ──────────────────────────────────────────────────
const resizeTip = ref(null);
let _tipTimer = null;

function showResizeTip(msg) {
  resizeTip.value = msg;
  clearTimeout(_tipTimer);
  _tipTimer = setTimeout(() => (resizeTip.value = null), 1200);
}

function startImageResize(e) {
  store.selectBlock(props.block.id);
  e.target.setPointerCapture(e.pointerId);

  const startX  = e.clientX;
  const current = parseInt(props.block.props.image_width) || 160;

  function onMove(ev) {
    const delta = ev.clientX - startX;
    // If image is on the right, drag direction is mirrored
    const sign  = props.block.props.image_position === "right" ? -1 : 1;
    const raw   = current + sign * delta;
    const clamped = Math.max(60, Math.min(400, Math.round(raw / 10) * 10)); // 10px snap
    store.updateBlockProps(props.block.id, { image_width: `${clamped}px` });
    showResizeTip(`⟺ ${clamped}px`);
  }

  function onUp() {
    e.target.removeEventListener("pointermove", onMove);
    e.target.removeEventListener("pointerup",   onUp);
  }

  e.target.addEventListener("pointermove", onMove);
  e.target.addEventListener("pointerup",   onUp);
}
</script>
