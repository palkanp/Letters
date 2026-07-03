<template>
  <div ref="el" class="relative overflow-hidden w-full h-full">
    <iframe
      v-if="previewHtml"
      :srcdoc="previewHtml"
      class="border-0 pointer-events-none absolute top-0 left-0"
      sandbox="allow-same-origin"
      :style="iframeStyle"
    />
    <div v-else class="absolute inset-0 flex items-center justify-center bg-surface-gray-3">
      <span v-if="loading" class="lucide-loader size-4 animate-spin text-ink-gray-4" aria-hidden="true" />
      <span v-else class="lucide-mail text-ink-gray-3" :class="iconClass" aria-hidden="true" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";

const props = defineProps({
  name: { type: String, required: true },
  iconClass: { type: String, default: "w-5 h-5" },
});

// The email's mobile breakpoint is @media (max-width:{email_width}px) — it
// stacks whenever the viewport is at or below the letter's own width. To render
// the thumbnail as DESKTOP we must give the iframe a viewport a bit WIDER than
// that letter's width, so the breakpoint doesn't fire. The width comes back
// from render_preview; until then we default to 600 + buffer. The email card
// stays centred and the reset CSS paints the margin with the email's own
// background, so the extra width blends in.
const BREAKPOINT_BUFFER = 40;
const el = ref(null);
const previewHtml = ref(null);
const loading = ref(false);
const scale = ref(0.35);
const iframeWidth = ref(600 + BREAKPOINT_BUFFER);

const iframeStyle = computed(() => ({
  width: `${iframeWidth.value}px`,
  height: "800px",
  transform: `scale(${scale.value})`,
  transformOrigin: "top left",
}));

let observer = null;

async function fetchPreview() {
  if (previewHtml.value || loading.value) return;
  loading.value = true;
  try {
    const res = await frappe.call({
      method: "letters.letters.api.render_preview",
      args: { name: props.name },
    });
    let html = res.message?.html || null;
    if (html) {
      // Size the iframe viewport just above this letter's own width so the
      // mobile breakpoint (max-width:{email_width}) doesn't fire in the thumbnail.
      iframeWidth.value = (res.message?.email_width || 600) + BREAKPOINT_BUFFER;
      if (el.value) scale.value = el.value.offsetWidth / iframeWidth.value;
      const bg = res.message?.first_bg || "#ffffff";
      const reset = `<style>
html,body{margin:0!important;padding:0!important;background:${bg}!important;}
html{scrollbar-width:none!important;}html::-webkit-scrollbar{display:none!important;}
table.body-wrap{background:${bg}!important;}
table.body-wrap>tbody>tr>td{padding:0!important;background:${bg}!important;}
table.email-card{background-color:${bg}!important;}
table.email-card>tbody>tr>td{font-size:0!important;line-height:0!important;}
</style>`;
      html = html.includes("</head>") ? html.replace("</head>", `${reset}</head>`) : reset + html;
    }
    previewHtml.value = html;
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
