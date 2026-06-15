<template>
  <div ref="el" class="relative overflow-hidden bg-white w-full h-full">
    <iframe
      v-if="previewHtml"
      :srcdoc="previewHtml"
      class="border-0 pointer-events-none absolute top-0 left-0"
      sandbox="allow-same-origin"
      :style="iframeStyle"
    />
    <div v-else class="absolute inset-0 flex items-center justify-center bg-surface-gray-3">
      <FeatherIcon v-if="loading" name="loader" class="w-4 h-4 animate-spin text-ink-gray-4" />
      <FeatherIcon v-else name="mail" class="text-ink-gray-3" :class="iconClass" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { FeatherIcon } from "frappe-ui";

const props = defineProps({
  name: { type: String, required: true },
  // icon size class for the fallback, e.g. "w-5 h-5" or "w-8 h-8"
  iconClass: { type: String, default: "w-5 h-5" },
});

const IFRAME_WIDTH = 600;
const el = ref(null);
const previewHtml = ref(null);
const loading = ref(false);
const scale = ref(0.35);

const iframeStyle = computed(() => ({
  width: `${IFRAME_WIDTH}px`,
  height: "800px",
  transform: `scale(${scale.value})`,
  transformOrigin: "top left",
}));

let observer = null;

async function fetchPreview() {
  if (previewHtml.value || loading.value) return;
  loading.value = true;
  if (el.value) scale.value = el.value.offsetWidth / IFRAME_WIDTH;
  try {
    const res = await frappe.call({
      method: "letters.letters.api.render_preview",
      args: { name: props.name },
    });
    previewHtml.value = res.message?.html || null;
  } catch {
    // leave null, fallback icon shows
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting) {
        observer?.disconnect();
        fetchPreview();
      }
    },
    { threshold: 0.1 },
  );
  if (el.value) observer.observe(el.value);
});

onUnmounted(() => observer?.disconnect());
</script>
