<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/80">
    <div class="bg-surface-base border-outline-gray-2 border rounded-2xl shadow-2xl w-[900px] max-h-[85vh] flex flex-col overflow-hidden">

      <!-- Header -->
      <div class="border-outline-gray-2 flex-shrink-0 px-6 py-4 border-b flex items-center justify-between gap-4">
        <div>
          <h2 class="text-ink-gray-9 text-base font-semibold">New Letter</h2>
          <p class="text-ink-gray-5 text-xs mt-0.5">Start from a template or begin with a blank canvas.</p>
        </div>
        <Button variant="ghost" icon="lucide-x" size="sm" class="flex-shrink-0" aria-label="Close" @click="$emit('close')" />
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
          <!-- Blank tile: single always-visible action, no hover overlay needed -->
          <div
            role="button"
            tabindex="0"
            class="flex flex-col gap-0 rounded-xl border-2 border-dashed border-outline-gray-2 overflow-hidden transition-colors hover:border-blue-500 cursor-pointer select-none"
            :class="{ 'pointer-events-none opacity-60': creating }"
            @click="pick(blankBlocks)"
            @keydown.enter="pick(blankBlocks)"
          >
            <div class="bg-surface-gray-2 h-48 flex flex-col items-center justify-center gap-2">
              <div class="bg-surface-base border-outline-gray-2 w-10 h-10 rounded-full border-2 flex items-center justify-center">
                <span class="lucide-plus size-5 text-ink-gray-5" aria-hidden="true" />
              </div>
              <span class="text-ink-gray-5 text-xs">Blank canvas</span>
            </div>
            <div class="border-outline-gray-2 px-4 py-2.5 border-t">
              <p class="text-ink-gray-9 text-sm font-medium">Blank page</p>
            </div>
          </div>

          <!-- Template tiles: hover overlay reveals Select/Preview. Overlay is
               pointer-events-none while hidden so it never eats the first
               click before hover state applies (that caused a double-click
               bug in an earlier version). -->
          <div
            v-for="tpl in templates"
            :key="tpl.name"
            class="group flex flex-col gap-0 rounded-xl border-2 border-outline-gray-2 overflow-hidden transition-colors hover:border-blue-500"
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

              <div
                class="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black/60 opacity-0 pointer-events-none transition-opacity group-hover:opacity-100 group-hover:pointer-events-auto"
              >
                <Button
                  label="Select Template"
                  variant="solid"
                  theme="gray"
                  size="sm"
                  :disabled="creating"
                  @click="pick(JSON.parse(tpl.blocks_json || '[]'))"
                />
                <Button
                  label="Preview"
                  variant="subtle"
                  theme="gray"
                  size="sm"
                  :disabled="!tpl.preview_html"
                  @click="previewTemplate = tpl"
                />
              </div>
            </div>
            <div class="border-outline-gray-2 px-4 py-2.5 border-t">
              <p class="text-ink-gray-9 text-sm font-medium truncate">{{ tpl.title }}</p>
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

  <!-- Full-size template preview -->
  <div v-if="previewTemplate" class="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 px-4 py-8" @click.self="previewTemplate = null">
    <div class="bg-surface-base border-outline-gray-2 border rounded-2xl shadow-2xl w-[720px] max-h-full flex flex-col overflow-hidden">
      <div class="border-outline-gray-2 flex-shrink-0 px-6 py-4 border-b flex items-center justify-between gap-4">
        <p class="text-ink-gray-9 text-base font-semibold">{{ previewTemplate.title }}</p>
        <div class="flex items-center gap-2">
          <Button
            label="Use template"
            variant="solid"
            size="sm"
            :disabled="creating"
            @click="pick(JSON.parse(previewTemplate.blocks_json || '[]'))"
          />
          <Button variant="ghost" icon="lucide-x" size="sm" aria-label="Close preview" @click="previewTemplate = null" />
        </div>
      </div>
      <div class="flex-1 overflow-y-auto">
        <iframe
          :srcdoc="injectReset(previewTemplate.preview_html, firstBgColor(previewTemplate))"
          class="w-full border-none"
          style="height: 80vh;"
          sandbox="allow-same-origin"
        />
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

// Above the email's mobile breakpoint (@media max-width:600px is inclusive),
// so template thumbnails render as desktop, not stacked mobile. See
// LetterThumbnail.vue for the full rationale.
const IFRAME_WIDTH = 640;
const tileRef = ref(null);
const previewTemplate = ref(null);

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
