<template>
  <div class="letters-builder flex flex-col bg-gray-100 font-sans overflow-hidden" style="height: 100vh">

    <!-- ── Top bar ─────────────────────────────────────────────────────────── -->
    <header class="flex-shrink-0 h-12 bg-white border-b border-gray-200 flex items-center px-4 gap-3">

      <!-- Layers toggle -->
      <button
        type="button"
        title="Layers"
        class="w-8 h-8 flex items-center justify-center rounded-lg transition-colors flex-shrink-0"
        :class="showLayers ? 'bg-gray-900 text-white' : 'text-gray-400 hover:text-gray-700 hover:bg-gray-100'"
        @click="showLayers = !showLayers"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="2" y="3" width="12" height="1.5" rx="0.75" fill="currentColor"/>
          <rect x="2" y="7.25" width="12" height="1.5" rx="0.75" fill="currentColor"/>
          <rect x="2" y="11.5" width="12" height="1.5" rx="0.75" fill="currentColor"/>
        </svg>
      </button>

      <div class="w-px h-5 bg-gray-200 flex-shrink-0"></div>

      <!-- Campaign name -->
      <TextInput
        v-model="editorStore.campaignName"
        placeholder="Campaign name…"
        class="w-44"
        size="sm"
      />

      <div class="flex-1 flex items-center gap-2">
        <TextInput
          v-model="subject"
          placeholder="Subject line…"
          class="flex-1 max-w-xs"
          size="sm"
        />
        <TextInput
          v-model="previewText"
          placeholder="Preview text…"
          class="flex-1 max-w-xs"
          size="sm"
        />
      </div>

      <!-- Feedback banners inline -->
      <span v-if="saveMsg" class="text-xs text-green-600 font-medium">{{ saveMsg }}</span>
      <span v-if="errorMsg" class="text-xs text-red-500 font-medium truncate max-w-xs" :title="errorMsg">{{ errorMsg }}</span>

      <!-- Actions -->
      <div class="flex items-center gap-1.5 flex-shrink-0">
        <Button variant="ghost" size="sm" :loading="previewing" title="Preview in new window" @click="openPreview">↗</Button>
        <Button variant="ghost" size="sm" :loading="saving" title="Save" @click="saveCampaign">
          <template #prefix><FeatherIcon name="upload-cloud" class="w-3.5 h-3.5" /></template>
          Save
        </Button>
        <Button variant="subtle" size="sm" :disabled="!editorStore.campaignDoc" @click="showSendModal = true">Send</Button>
      </div>
    </header>

    <!-- ── Body ──────────────────────────────────────────────────────────────── -->
    <div class="flex flex-1 overflow-hidden relative">

      <!-- Layers drawer (slide-in overlay) -->
      <transition
        enter-active-class="transition-transform duration-200 ease-out"
        enter-from-class="-translate-x-full"
        enter-to-class="translate-x-0"
        leave-active-class="transition-transform duration-150 ease-in"
        leave-from-class="translate-x-0"
        leave-to-class="-translate-x-full"
      >
        <div
          v-if="showLayers"
          class="absolute left-0 top-0 bottom-0 z-30 w-56 bg-white border-r border-gray-200 flex flex-col shadow-xl"
        >
          <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 flex-shrink-0">
            <span class="text-xs font-semibold text-gray-500 uppercase tracking-widest">Layers</span>
            <button
              type="button"
              class="w-6 h-6 flex items-center justify-center rounded-md text-gray-400 hover:text-gray-700 hover:bg-gray-100 text-sm"
              @click="showLayers = false"
            >✕</button>
          </div>
          <LayersPanel />
        </div>
      </transition>

      <!-- Backdrop for layers drawer -->
      <div
        v-if="showLayers"
        class="absolute inset-0 z-20"
        @click="showLayers = false"
      ></div>

      <!-- Canvas -->
      <main
        class="flex-1 overflow-y-auto p-6"
        @dragover.prevent
        @drop="onCanvasDrop"
        @click="editorStore.selectBlock(null)"
      >
        <div class="mx-auto bg-white shadow-sm" style="max-width:600px;min-height:200px">

          <!-- Empty state -->
          <div
            v-if="!editorStore.blocks.length"
            class="border-2 border-dashed border-gray-300 rounded-xl p-16 text-center text-gray-400 bg-white/50 select-none"
          >
            <div class="text-4xl mb-3 opacity-40">✦</div>
            <p class="text-sm font-medium mb-4">Your canvas is empty</p>
            <button
              type="button"
              class="inline-flex items-center gap-1.5 px-4 py-2 bg-gray-900 text-white text-sm font-semibold rounded-lg hover:bg-gray-700 transition-colors"
              @click.stop="openPicker(-1)"
            >
              <span class="text-base leading-none">+</span> Add first block
            </button>
          </div>

          <!-- Block list with inline adders -->
          <template v-else>
            <!-- Adder before first block -->
            <BlockAdderRow :after-index="-1" @open="openPicker" />

            <template v-for="(block, index) in editorStore.blocks" :key="block.id">
              <component
                :is="blockComponent(block.type)"
                :block="block"
                :index="index"
              />
              <!-- Adder after each block -->
              <BlockAdderRow :after-index="index" @open="openPicker" />
            </template>
          </template>
        </div>
      </main>

      <!-- Right: Inspector -->
      <Inspector />

    </div>
  </div>

  <!-- ── Block Picker overlay ───────────────────────────────────────────────── -->
  <Teleport to="body">
    <div
      v-if="pickerAfterIndex !== null"
      class="fixed inset-0 z-50 flex items-center justify-center"
      style="background: rgba(0,0,0,0.25); backdrop-filter: blur(2px);"
      @click.self="closePicker"
    >
      <div class="bg-white rounded-2xl shadow-2xl border border-gray-100 p-5 w-80">
        <div class="flex items-center justify-between mb-4">
          <span class="text-xs font-semibold text-gray-400 uppercase tracking-widest">Add a block</span>
          <button
            type="button"
            class="w-6 h-6 flex items-center justify-center rounded-md text-gray-400 hover:text-gray-700 hover:bg-gray-100 text-sm"
            @click="closePicker"
          >✕</button>
        </div>
        <div class="grid grid-cols-3 gap-1.5">
          <button
            v-for="b in availableBlocks"
            :key="b.type"
            type="button"
            class="flex flex-col items-center gap-1.5 px-2 py-3 rounded-xl text-gray-600 hover:bg-gray-900 hover:text-white transition-colors group"
            @click="insertBlock(b.type)"
          >
            <span class="text-xl leading-none">{{ b.icon }}</span>
            <span class="text-xs font-medium leading-none">{{ b.label }}</span>
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <SendModal
    v-if="showSendModal"
    :campaign-name="editorStore.campaignName"
    :campaign-doc="editorStore.campaignDoc"
    @close="showSendModal = false"
    @sent="onSent"
  />
</template>

<script setup>
import { ref, defineAsyncComponent, onMounted } from "vue";
import { Button, TextInput, FeatherIcon } from "frappe-ui";
import { useEditorStore } from "../stores/editor";
import Inspector from "../components/Inspector.vue";
import LayersPanel from "../components/LayersPanel.vue";
import SendModal from "../components/SendModal.vue";
import BlockAdderRow from "../components/BlockAdderRow.vue";

const editorStore = useEditorStore();
const saving     = ref(false);
const previewing = ref(false);
const showSendModal = ref(false);
const showLayers = ref(false);
const saveMsg    = ref("");
const errorMsg   = ref("");
const subject    = ref("");
const previewText = ref("");

// null = closed; any number = open, insert after that index
const pickerAfterIndex = ref(null);

// ── Error helper ──────────────────────────────────────────────────────────────
function describeError(e) {
  try {
    const msgs = e?._server_messages;
    if (msgs) {
      const parsed = JSON.parse(msgs);
      const first = parsed[0];
      try { return JSON.parse(first).message || first; } catch { return first; }
    }
  } catch { /* fall through */ }
  return e?.message || e?.exc || "Something went wrong.";
}

// ── Load campaign from URL ?name=xxx ─────────────────────────────────────────
const urlParams   = new URLSearchParams(window.location.search);
const initialName = urlParams.get("name");

onMounted(async () => {
  if (initialName) await loadCampaign(initialName);
});

async function loadCampaign(name) {
  try {
    const res = await frappe.call({ method: "letters.letters.api.get_campaign", args: { name } });
    const doc = res.message;
    editorStore.loadFromDoc(doc);
    subject.value     = doc.subject || "";
    previewText.value = doc.preview_text || "";
  } catch (e) {
    errorMsg.value = "Couldn't load campaign: " + describeError(e);
  }
}

// ── Save ──────────────────────────────────────────────────────────────────────
async function saveCampaign() {
  saving.value   = true;
  saveMsg.value  = "";
  errorMsg.value = "";
  try {
    const res = await frappe.call({
      method: "letters.letters.api.save_campaign",
      args: {
        name:         editorStore.campaignDoc?.name || null,
        title:        editorStore.campaignName || "Untitled Campaign",
        subject:      subject.value,
        preview_text: previewText.value,
        blocks:       JSON.stringify(editorStore.blocks.map(({ id: _id, ...rest }) => rest)),
      },
    });
    const saved = res.message;
    if (!editorStore.campaignDoc) {
      editorStore.campaignDoc = saved;
      const url = new URL(window.location.href);
      url.searchParams.set("name", saved.name);
      window.history.replaceState({}, "", url.toString());
    } else {
      editorStore.campaignDoc.name = saved.name;
    }
    saveMsg.value = "Saved!";
    setTimeout(() => (saveMsg.value = ""), 2500);
  } catch (e) {
    errorMsg.value = "Couldn't save: " + describeError(e);
  } finally {
    saving.value = false;
  }
}

// ── Preview ───────────────────────────────────────────────────────────────────
async function openPreview() {
  previewing.value = true;
  errorMsg.value   = "";
  try {
    const res = await frappe.call({
      method: "letters.letters.api.render_preview",
      args: {
        blocks:       JSON.stringify(editorStore.blocks.map(({ id: _id, ...rest }) => rest)),
        preview_text: previewText.value,
      },
    });
    const html          = res.message.html;
    const campaignTitle = editorStore.campaignName || "Email Preview";

    const toolbar = `
<style>
  #__preview-toolbar {
    position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
    display: flex; align-items: center; gap: 4px;
    background: #111827; border-radius: 9999px;
    padding: 6px 10px; box-shadow: 0 8px 32px rgba(0,0,0,.5);
    z-index: 9999; font-family: -apple-system, sans-serif;
  }
  #__preview-toolbar span {
    color: #9ca3af; font-size: 11px; padding: 0 8px 0 4px;
    border-right: 1px solid #374151; margin-right: 4px;
  }
  #__preview-toolbar button {
    color: #e5e7eb; background: none; border: none; cursor: pointer;
    font-size: 12px; padding: 5px 12px; border-radius: 6px; transition: background .15s;
  }
  #__preview-toolbar button:hover { background: #1f2937; }
  #__preview-toolbar button.active { background: #374151; color: #fff; }
</style>
<div id="__preview-toolbar">
  <span>${campaignTitle}</span>
  <button class="active" onclick="setMode('desktop', this)">🖥 Desktop</button>
  <button onclick="setMode('mobile', this)">📱 Mobile</button>
</div>
<script>
  function setMode(mode, btn) {
    document.querySelectorAll('#__preview-toolbar button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.body.style.maxWidth = mode === 'mobile' ? '390px' : '';
    document.body.style.margin   = mode === 'mobile' ? '0 auto' : '';
  }
<\/script>`;

    const fullHtml = html.replace("</body>", toolbar + "\n</body>");
    const win = window.open("", "_blank", "noopener");
    if (win) {
      win.document.write(fullHtml);
      win.document.close();
      win.document.title = campaignTitle + " — Preview";
    } else {
      errorMsg.value = "Pop-up blocked — allow pop-ups to use Preview.";
    }
  } catch (e) {
    errorMsg.value = "Preview failed: " + describeError(e);
  } finally {
    previewing.value = false;
  }
}

// ── Send ──────────────────────────────────────────────────────────────────────
function onSent() {
  showSendModal.value = false;
  saveMsg.value = "Campaign sent!";
  setTimeout(() => (saveMsg.value = ""), 3000);
}

// ── Block picker ──────────────────────────────────────────────────────────────
const availableBlocks = [
  { type: "hero",          label: "Hero",       icon: "◉" },
  { type: "text",          label: "Text",        icon: "¶" },
  { type: "image",         label: "Image",       icon: "◻" },
  { type: "image_text",    label: "Img + Text",  icon: "▣" },
  { type: "button",        label: "Button",      icon: "▷" },
  { type: "columns",       label: "Columns",     icon: "⊞" },
  { type: "container",     label: "Container",   icon: "▢" },
  { type: "section_label", label: "Label",       icon: "§" },
  { type: "divider",       label: "Divider",     icon: "—" },
  { type: "footer",        label: "Footer",      icon: "≡" },
];

function openPicker(afterIndex) {
  pickerAfterIndex.value = afterIndex;
}
function closePicker() {
  pickerAfterIndex.value = null;
}
function insertBlock(type) {
  editorStore.addBlock(type, pickerAfterIndex.value);
  closePicker();
}

// ── Block components (lazy) ───────────────────────────────────────────────────
const blockComponentCache = {};
function blockComponent(type) {
  if (!blockComponentCache[type]) {
    blockComponentCache[type] = defineAsyncComponent(
      () => import(`../components/blocks/${type}.vue`)
    );
  }
  return blockComponentCache[type];
}

// ── Drag-to-canvas drop (still supported — appends at end) ────────────────────
let dragging = null;
function onCanvasDrop() {
  if (dragging) {
    editorStore.addBlock(dragging.type);
    dragging = null;
  }
}
</script>
