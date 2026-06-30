<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/80">
    <div class="bg-white border-outline-gray-2 border rounded-2xl shadow-2xl w-[900px] max-h-[85vh] flex flex-col overflow-hidden letters-picker-shell" style="color-scheme: light">

      <!-- Header -->
      <div class="border-outline-gray-2 flex-shrink-0 px-8 pt-7 pb-5 border-b flex items-start justify-between gap-4">
        <div>
          <h2 class="text-ink-gray-9 text-xl font-semibold">New Letter</h2>
          <p class="text-ink-gray-5 text-sm mt-1">Start from a template or begin with a blank canvas.</p>
        </div>
        <Button variant="ghost" icon="lucide-x" size="sm" class="flex-shrink-0 mt-0.5" aria-label="Close" @click="$emit('close')" />
      </div>

      <!-- Grid -->
      <div class="flex-1 overflow-y-auto px-8 py-6">
        <div v-if="loading" class="grid grid-cols-3 gap-5">
          <div v-for="i in 6" :key="i" class="rounded-xl border border-outline-gray-1 overflow-hidden animate-pulse">
            <div class="bg-surface-gray-2 h-48" />
            <div class="p-4 space-y-2">
              <div class="h-3.5 bg-surface-gray-3 rounded w-1/2" />
              <div class="h-2.5 bg-surface-gray-2 rounded w-3/4" />
            </div>
          </div>
        </div>

        <!-- Error state -->
        <div v-else-if="loadError" class="flex flex-col items-center justify-center py-16 gap-4">
          <p class="text-sm text-ink-gray-6">Couldn't load templates.</p>
          <Button variant="subtle" size="sm" label="Try again" icon="refresh-cw" @click="loadTemplates" />
        </div>

        <div v-else class="grid grid-cols-3 gap-5">
          <!-- Blank tile -->
          <div class="group flex flex-col gap-0 rounded-xl border-2 border-dashed border-outline-gray-2 overflow-hidden transition-all hover:border-blue-500">
            <div class="relative bg-surface-gray-2 h-48 flex flex-col items-center justify-center gap-2 overflow-hidden">
              <div class="bg-surface-base border-outline-gray-2 w-10 h-10 rounded-full border-2 flex items-center justify-center">
                <span class="lucide-plus size-5 text-ink-gray-5" aria-hidden="true" />
              </div>
              <span class="text-ink-gray-5 text-xs">Blank canvas</span>
              <!-- Hover overlay -->
              <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <Button label="Start blank" :disabled="creating" @click="pick(blankBlocks)" />
              </div>
            </div>
            <div class="border-outline-gray-2 px-4 py-3 border-t">
              <p class="text-ink-gray-9 text-sm font-semibold">Blank</p>
            </div>
          </div>

          <!-- Template tiles -->
          <div
            v-for="tpl in templates"
            :key="tpl.name"
            class="group flex flex-col gap-0 rounded-xl border-2 border-outline-gray-2 overflow-hidden transition-all hover:border-blue-500"
          >
            <div ref="tileRef" class="relative h-48 overflow-hidden">
              <iframe
                v-if="tpl.preview_html"
                :srcdoc="injectReset(tpl.preview_html, firstBgColor(tpl))"
                class="absolute top-0 left-0 border-none pointer-events-none"
                sandbox="allow-same-origin"
                :style="tileIframeStyle"
              />
              <div v-else class="w-full h-full bg-surface-gray-2 flex items-center justify-center">
                <span class="text-xs text-ink-gray-4">Preview unavailable</span>
              </div>
              <!-- Hover overlay -->
              <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <Button label="Use template" :disabled="creating" @click="pick(JSON.parse(tpl.blocks_json || '[]'))" />
              </div>
            </div>
            <div class="border-outline-gray-2 px-4 py-3 border-t">
              <p class="text-ink-gray-9 text-sm font-semibold">{{ tpl.title }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div v-if="creating" class="border-outline-gray-2 flex-shrink-0 px-8 py-4 border-t flex items-center gap-3">
        <div class="w-4 h-4 border-2 border-outline-gray-3 border-t-blue-500 rounded-full animate-spin" />
        <span class="text-ink-gray-5 text-sm">Setting up your letter…</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { Button } from "frappe-ui";

const props = defineProps({
  submit: { type: Function, required: true },
});
defineEmits(["close"]);

const IFRAME_WIDTH = 600;
const tileRef = ref(null);

const tileIframeStyle = computed(() => {
  const containerW = tileRef.value?.offsetWidth || 265;
  const scale = containerW / IFRAME_WIDTH;
  return {
    width: `${IFRAME_WIDTH}px`,
    height: "1500px",
    transform: `scale(${scale})`,
    transformOrigin: "top left",
  };
});

// The preview iframe is CSS-scaled (transform: scale), which introduces a
// sub-pixel seam between adjacent top-level block tables. That seam reveals
// whatever sits *behind* the email content. To make it invisible, paint
// html/body/body-wrap/email-card with the template's own dominant background
// color so the bleed-through matches the email instead of the light modal.
function previewReset(bg) {
  return `<style>
html,body{margin:0!important;padding:0!important;background:${bg}!important;}
html{scrollbar-width:none!important;}html::-webkit-scrollbar{display:none!important;}
table.body-wrap{background:${bg}!important;}
table.body-wrap>tbody>tr>td{padding:0!important;background:${bg}!important;}
table.email-card{background-color:${bg}!important;}
table.email-card>tbody>tr>td{font-size:0!important;line-height:0!important;}
</style>`;
}

// Find the first block's background color (depth-first), defaulting to white.
function firstBgColor(tpl) {
  try {
    const blocks = JSON.parse(tpl.blocks_json || "[]");
    const walk = (list) => {
      for (const b of list) {
        const c = b?.props?.background_color;
        if (c && c !== "transparent") return c;
        const found = walk(b?.children || []);
        if (found) return found;
      }
      return null;
    };
    return walk(blocks) || "#ffffff";
  } catch {
    return "#ffffff";
  }
}

function injectReset(html, bg = "#ffffff") {
  if (!html) return html;
  const reset = previewReset(bg);
  return html.includes("</head>")
    ? html.replace("</head>", `${reset}</head>`)
    : reset + html;
}

const loading = ref(true);
const creating = ref(false);
const loadError = ref(false);
const templates = ref([]);

const blankBlocks = [];

async function loadTemplates() {
  loading.value = true;
  loadError.value = false;
  try {
    const res = await frappe.call({ method: "letters.letters.api.get_templates" });
    templates.value = res.message || [];
  } catch {
    loadError.value = true;
  } finally {
    loading.value = false;
  }
}

onMounted(loadTemplates);

async function pick(blocks) {
  if (creating.value) return;
  creating.value = true;
  try {
    await props.submit(blocks);
  } catch (e) {
    creating.value = false;
    throw e;
  }
}
</script>
