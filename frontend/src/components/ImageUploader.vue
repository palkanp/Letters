<template>
  <!-- frappe-ui FileUploader drives the actual upload (Frappe file API). We render
       our own dropzone in its default slot and keep drag-and-drop by forwarding
       dropped files into the uploader's hidden <input>. -->
  <FileUploader
    ref="uploader"
    :file-types="'image/png,image/jpeg,image/gif,image/webp'"
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
            <Button
              variant="ghost"
              size="sm"
              class="absolute top-1.5 right-1.5 opacity-0 group-hover/img:opacity-100
                     transition-opacity !bg-ink-gray-9/60 !text-ink-white backdrop-blur-sm"
              @click.stop="openFileSelector"
            >Replace</Button>
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
          class="w-full border-2 border-dashed rounded-lg flex flex-col items-center justify-center text-center cursor-pointer transition-colors select-none px-3"
          :class="[compact ? 'gap-0.5 py-2' : 'gap-1.5 py-6', !compact && heightClass, isDragging
            ? 'border-outline-gray-4 bg-surface-gray-2'
            : 'border-outline-gray-2 bg-surface-gray-1 hover:border-outline-gray-3 hover:bg-surface-gray-2']"
          @click.stop="openFileSelector"
          @dragover.prevent.stop="isDragging = true"
          @dragleave.stop="isDragging = false"
          @drop.prevent.stop="onDrop"
        >
          <span v-if="uploading" class="text-xs text-ink-gray-4">Uploading {{ progress }}%…</span>
          <template v-else>
            <span :class="compact ? 'lucide-image size-4' : 'lucide-image size-6'" class="text-ink-gray-4" aria-hidden="true" />
            <span class="text-xs text-ink-gray-6 font-medium text-center leading-tight">{{ compact ? 'Add logo' : 'Click or drop image' }}</span>
            <span v-if="!compact" class="text-xs text-ink-gray-4 text-center leading-tight">PNG, JPG or GIF · max 5 MB</span>
          </template>
        </div>
      </div>
    </template>
  </FileUploader>
</template>

<script setup>
import { ref } from "vue";
import { FileUploader, Button, toast } from "frappe-ui";

const props = defineProps({
  url:         { type: String, default: "" },
  alt:         { type: String, default: "" },
  heightClass: { type: String, default: "h-44" },
  replaceClass:{ type: String, default: "" },
  hideReplace: { type: Boolean, default: false },
  compact:     { type: Boolean, default: false },
});

const emit = defineEmits(["uploaded"]);

const uploader   = ref(null);
const isDragging = ref(false);

// SVG is rejected outright: Gmail, Outlook, and Yahoo all fail to render SVG
// <img> sources (only Apple Mail does), so it would ship as a broken image to
// most recipients. WebP isn't recommended as the fallback here even though we
// allow it below — it's broken (not just non-animating, like GIF) in Outlook
// desktop, so PNG/JPG/GIF are the actually-safe options for this message.
//
// A string return here also becomes FileUploader's internal `error` state,
// but we don't render that inline (it used to visibly distort the block's
// layout in the canvas) — the toast is the only user-facing message. The
// string return still matters: it's what makes FileUploader treat the file
// as rejected and skip the actual upload.
function validateImage(file) {
  if (!file.type?.startsWith("image/")) {
    toast.error("Please choose an image file.");
    return "Please choose an image file.";
  }
  if (file.type === "image/svg+xml") {
    const message = "SVG images don't display in Gmail, Outlook, or Yahoo Mail. Please use PNG, JPG, or GIF instead.";
    toast.error(message);
    return message;
  }
  if (file.size > 5 * 1024 * 1024) {
    const message = "Image must be under 5 MB. Please resize or compress before uploading.";
    toast.error(message);
    return message;
  }
  if (file.type === "image/webp") {
    toast.warning("WebP images won't display in Outlook desktop — PNG or JPG is safer if that audience matters.");
  }
  return null;
}

function onSuccess(fileDoc) {
  const fileUrl = fileDoc?.file_url || fileDoc?.message?.file_url;
  if (fileUrl) emit("uploaded", fileUrl);
}

function onFailure(err) {
  toast.error(err?.message || "Upload failed");
}

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
