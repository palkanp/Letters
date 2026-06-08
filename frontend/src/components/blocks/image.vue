<template>
  <BlockWrapper :block="block" :index="index">
    <div class="px-8 py-4" :style="{ backgroundColor: block.props.background_color }">

      <!-- Image or upload zone -->
      <img
        v-if="block.props.image_url"
        :src="block.props.image_url"
        :alt="block.props.alt || ''"
        class="w-full block"
        :style="{
          border: block.props.border || 'none',
          borderRadius: block.props.border_radius || '0',
        }"
      />

      <!-- Upload zone -->
      <div
        v-else
        class="w-full h-44 border-2 border-dashed rounded-lg flex flex-col items-center justify-center gap-2 cursor-pointer transition-colors select-none"
        :class="isDragging
          ? 'border-gray-500 bg-gray-100'
          : 'border-gray-300 bg-gray-50 hover:border-gray-400 hover:bg-gray-100'"
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

      <!-- Replace link -->
      <button
        v-if="block.props.image_url"
        type="button"
        class="mt-1 text-xs text-gray-400 hover:text-gray-600 transition-colors"
        @click.stop="triggerFileInput"
      >Replace image</button>

      <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onFileSelect" />
      <p v-if="uploadError" class="mt-1 text-xs text-red-500">{{ uploadError }}</p>

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
import { ref } from "vue";
import BlockWrapper from "../BlockWrapper.vue";
import { useEditorStore } from "../../stores/editor";

const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();
function update(key, val) { store.updateBlockProps(props.block.id, { [key]: val }); }

const fileInput   = ref(null);
const uploading   = ref(false);
const uploadError = ref("");
const isDragging  = ref(false);

function triggerFileInput() { fileInput.value?.click(); }
function onFileSelect(e) {
  const file = e.target.files?.[0];
  if (file) uploadFile(file);
}
function onFileDrop(e) {
  isDragging.value = false;
  const file = e.dataTransfer?.files?.[0];
  if (file && file.type.startsWith("image/")) uploadFile(file);
}

async function uploadFile(file) {
  uploading.value = true;
  uploadError.value = "";
  try {
    const fd = new FormData();
    fd.append("file", file, file.name);
    fd.append("is_private", "0");
    fd.append("doctype", "Email Campaign");
    const csrf = window?.frappe?.csrf_token || "";
    const res = await fetch("/api/method/upload_file", {
      method: "POST",
      headers: { "X-Frappe-CSRF-Token": csrf, "Accept": "application/json" },
      body: fd,
    });
    const data = await res.json();
    if (data.exc || data._server_messages) throw new Error("Upload rejected by server");
    const url = data?.message?.file_url;
    if (!url) throw new Error("No file URL in response");
    update("image_url", url);
  } catch (err) {
    uploadError.value = err.message || "Upload failed";
  } finally {
    uploading.value = false;
    if (fileInput.value) fileInput.value.value = "";
  }
}
</script>
