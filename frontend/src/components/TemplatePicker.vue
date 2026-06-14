<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/80">
    <div class="bg-surface-base border-outline-gray-2 border rounded-2xl shadow-2xl w-[900px] max-h-[85vh] flex flex-col overflow-hidden">

      <!-- Header -->
      <div class="border-outline-gray-2 flex-shrink-0 px-8 pt-7 pb-5 border-b">
        <h2 class="text-ink-gray-9 text-xl font-semibold">New Campaign</h2>
        <p class="text-ink-gray-5 text-sm mt-1">Start from a template or begin with a blank canvas.</p>
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

        <div v-else class="grid grid-cols-3 gap-5">
          <!-- Blank tile -->
          <div class="group flex flex-col gap-0 rounded-xl border-2 border-dashed border-outline-gray-2 overflow-hidden transition-all hover:border-blue-500">
            <div class="relative bg-surface-gray-2 h-48 flex flex-col items-center justify-center gap-2 overflow-hidden">
              <div class="bg-surface-base border-outline-gray-2 w-10 h-10 rounded-full border-2 flex items-center justify-center">
                <svg class="text-ink-gray-5 w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
                </svg>
              </div>
              <span class="text-ink-gray-5 text-xs">Blank canvas</span>
              <!-- Hover overlay -->
              <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <Button label="Start blank" :disabled="creating" @click="pick(blankBlocks)" />
              </div>
            </div>
            <div class="border-outline-gray-2 px-4 py-3 border-t">
              <p class="text-ink-gray-9 text-sm font-semibold">Blank</p>
              <p class="text-ink-gray-5 text-xs mt-0.5">Header and footer only</p>
            </div>
          </div>

          <!-- Template tiles -->
          <div
            v-for="tpl in templates"
            :key="tpl.name"
            class="group flex flex-col gap-0 rounded-xl border-2 border-outline-gray-2 overflow-hidden transition-all hover:border-blue-500"
          >
            <div class="relative h-48 bg-white overflow-hidden">
              <iframe
                v-if="tpl.preview_html"
                :srcdoc="tpl.preview_html"
                class="absolute top-0 left-0 border-none pointer-events-none"
                sandbox="allow-same-origin"
                :style="{ height: '1500px', transform: 'scale(0.46)', transformOrigin: 'top left', width: '217%' }"
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
        <div class="w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
        <span class="text-ink-gray-5 text-sm">Setting up your campaign…</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { Button } from "frappe-ui";

const props = defineProps({
  submit: { type: Function, required: true },
});

const loading = ref(true);
const creating = ref(false);
const templates = ref([]);

const blankBlocks = [{ type: "header" }, { type: "footer" }];

onMounted(async () => {
  try {
    const res = await frappe.call({ method: "letters.letters.api.get_templates" });
    templates.value = res.message || [];
  } catch (e) {
    console.error("Failed to load templates", e);
  } finally {
    loading.value = false;
  }
});

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
