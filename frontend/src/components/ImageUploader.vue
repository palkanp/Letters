<template>
  <!-- frappe-ui FileUploader drives the actual upload (Frappe file API). We render
       our own dropzone in its default slot and keep drag-and-drop by forwarding
       dropped files into the uploader's hidden <input>. -->
  <FileUploader
    ref="uploader"
    :file-types="'image/*'"
    :upload-args="{ is_private: 0, folder: 'Home/Attachments' }"
    :validate-file="validateImage"
    @success="onSuccess"
    @failure="onFailure"
  >
    <template #default="{ uploading, progress, openFileSelector }">
      <div style="line-height:0;font-size:0;">

        <!-- Uploaded image — rendering delegated to the parent via slot -->
        <template v-if="url">
          <div v-if="!hideReplace" class="relative group/img" style="line-height:0;font-size:0;">
            <slot :url="url">
              <img :src="url" class="w-full block" :alt="alt" />
            </slot>
            <!-- Replace overlay — appears on hover -->
            <button
              type="button"
              class="absolute top-1.5 right-1.5 px-2 py-0.5 rounded text-xs font-medium
                     bg-black/60 text-white opacity-0 group-hover/img:opacity-100
                     transition-opacity backdrop-blur-sm"
              @click.stop="openFileSelector"
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
          @click.stop="openFileSelector"
          @dragover.prevent.stop="isDragging = true"
          @dragleave.stop="isDragging = false"
          @drop.prevent.stop="onDrop"
        >
          <span v-if="uploading" class="text-xs text-gray-400">Uploading {{ progress }}%…</span>
          <template v-else>
            <FeatherIcon name="image" class="w-6 h-6 text-gray-400" />
            <span class="text-xs text-gray-600 font-medium">Click or drop image</span>
            <span class="text-xs text-gray-400">PNG, JPG or WebP, max 5 MB</span>
          </template>
        </div>

        <p v-if="uploadError" class="mt-1 text-xs text-red-500">{{ uploadError }}</p>
      </div>
    </template>
  </FileUploader>
</template>

<script setup>
import { ref } from "vue";
import { FileUploader, FeatherIcon } from "frappe-ui";

const props = defineProps({
  url:         { type: String, default: "" },
  alt:         { type: String, default: "" },
  heightClass: { type: String, default: "h-44" },   // dropzone height
  replaceClass:{ type: String, default: "" },        // extra classes for replace btn
  hideReplace: { type: Boolean, default: false },
});

const emit = defineEmits(["uploaded"]);

const uploader    = ref(null);
const isDragging  = ref(false);
const uploadError = ref("");

// Reject non-images / oversized files before they hit the network.
function validateImage(file) {
  if (!file.type?.startsWith("image/")) return "Please choose an image file.";
  if (file.size > 5 * 1024 * 1024) return "Image must be under 5 MB. Please resize or compress before uploading.";
  uploadError.value = "";
  return null; // valid
}

// FileUploader emits `success` with the created File doc → grab its file_url.
function onSuccess(fileDoc) {
  const fileUrl = fileDoc?.file_url || fileDoc?.message?.file_url;
  if (fileUrl) emit("uploaded", fileUrl);
}

function onFailure(err) {
  uploadError.value = err?.message || "Upload failed";
}

// Drag-and-drop: forward the dropped file into FileUploader's hidden <input>
// so it runs through the exact same validate + upload pipeline as click-to-select.
function onDrop(e) {
  isDragging.value = false;
  const file = e.dataTransfer?.files?.[0];
  if (!file) return;
  const input = uploader.value?.inputRef?.();
  if (!input) return;
  const dt = new DataTransfer();
  dt.items.add(file);
  input.files = dt.files;
  input.dispatchEvent(new Event("change", { bubbles: true }));
}
</script>
