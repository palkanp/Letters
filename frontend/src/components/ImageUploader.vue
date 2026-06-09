<template>
  <div>
    <!-- Hidden native file input (shared by dropzone + replace button) -->
    <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onFileSelect" />

    <!-- Uploaded image — rendering delegated to the parent via slot so each
         block controls its own framing (full-width, fixed-width, borders…) -->
    <template v-if="url">
      <div v-if="!hideReplace" class="relative group/img">
        <slot :url="url">
          <img :src="url" class="w-full block" :alt="alt" />
        </slot>
        <!-- Replace overlay — appears on hover, no extra height -->
        <button
          type="button"
          class="absolute top-1.5 right-1.5 px-2 py-0.5 rounded text-xs font-medium
                 bg-black/60 text-white opacity-0 group-hover/img:opacity-100
                 transition-opacity backdrop-blur-sm"
          @click.stop="triggerFileInput"
        >Replace</button>
      </div>
      <template v-else>
        <slot :url="url">
          <img :src="url" class="w-full block" :alt="alt" />
        </slot>
      </template>
    </template>

    <!-- Empty state dropzone -->
    <div
      v-else
      class="w-full border-2 border-dashed rounded-lg flex flex-col items-center justify-center gap-2 cursor-pointer transition-colors select-none"
      :class="[heightClass, isDragging
        ? 'border-gray-500 bg-gray-100'
        : 'border-gray-300 bg-gray-50 hover:border-gray-400 hover:bg-gray-100']"
      @click.stop="triggerFileInput"
      @dragover.prevent.stop="isDragging = true"
      @dragleave.stop="isDragging = false"
      @drop.prevent.stop="onFileDrop"
    >
      <span v-if="uploading" class="text-xs text-gray-400">Uploading…</span>
      <template v-else>
        <span class="text-2xl">🖼</span>
        <span class="text-xs text-gray-600 font-medium">Click or drop image</span>
        <span class="text-xs text-gray-400">PNG, JPG, GIF, WebP</span>
      </template>
    </div>

    <p v-if="uploadError" class="mt-1 text-xs text-red-500">{{ uploadError }}</p>
  </div>
</template>

<script setup>
import { useImageUpload } from "../composables/useImageUpload";

const props = defineProps({
  url:         { type: String, default: "" },
  alt:         { type: String, default: "" },
  heightClass: { type: String, default: "h-44" },   // dropzone height
  replaceClass:{ type: String, default: "" },        // extra classes for replace btn
  hideReplace: { type: Boolean, default: false },
});

const emit = defineEmits(["uploaded"]);

const {
  fileInput, uploading, uploadError, isDragging,
  triggerFileInput, onFileSelect, onFileDrop,
} = useImageUpload((url) => emit("uploaded", url));
</script>
