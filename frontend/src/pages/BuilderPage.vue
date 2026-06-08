<template>
  <div class="letters-builder flex flex-col bg-gray-100 font-sans overflow-hidden" style="height: calc(100vh - 60px)">

    <!-- ── Top bar ─────────────────────────────────────────────────────────── -->
    <header class="flex-shrink-0 h-12 bg-white border-b border-gray-200 flex items-center px-4 gap-3">
      <!-- Campaign name -->
      <TextInput
        v-model="editorStore.campaignName"
        placeholder="Campaign name…"
        class="w-52"
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
        <Button variant="solid" theme="gray" size="sm" @click="saveCampaign" :loading="saving">Save</Button>
        <Button variant="subtle" size="sm" :disabled="!editorStore.campaignDoc" @click="showSendModal = true">Send</Button>
      </div>
    </header>

    <!-- ── Three-panel body ───────────────────────────────────────────────── -->
    <div class="flex flex-1 overflow-hidden">

      <!-- Left: Block Palette + Layers -->
      <aside class="w-52 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col overflow-hidden">
        <!-- Tabs -->
        <div class="flex border-b border-gray-200 flex-shrink-0">
          <button
            v-for="tab in ['Blocks', 'Layers']"
            :key="tab"
            type="button"
            class="flex-1 py-2.5 text-xs font-semibold transition-colors"
            :class="leftTab === tab
              ? 'text-gray-900 border-b-2 border-gray-900'
              : 'text-gray-400 hover:text-gray-600'"
            @click="leftTab = tab"
          >{{ tab }}</button>
        </div>

        <!-- Blocks list -->
        <div v-if="leftTab === 'Blocks'" class="p-3 flex flex-col gap-1 overflow-y-auto">
          <div
            v-for="block in availableBlocks"
            :key="block.type"
            class="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm text-gray-700 cursor-grab select-none hover:bg-gray-100 active:cursor-grabbing transition-colors border border-transparent hover:border-gray-200"
            draggable="true"
            @dragstart="onDragStart(block)"
          >
            <span class="text-gray-400 text-base leading-none w-4 text-center">{{ block.icon }}</span>
            <span class="font-medium">{{ block.label }}</span>
          </div>
        </div>

        <!-- Layers -->
        <div v-else class="flex-1 overflow-hidden flex flex-col">
          <LayersPanel />
        </div>
      </aside>

      <!-- Center: Canvas -->
      <main
        class="flex-1 overflow-y-auto p-6"
        @dragover.prevent
        @drop="onDrop"
        @click="editorStore.selectBlock(null)"
      >
        <div class="max-w-2xl mx-auto">
          <!-- Empty state -->
          <div
            v-if="!editorStore.blocks.length"
            class="border-2 border-dashed border-gray-300 rounded-xl p-20 text-center text-gray-400 text-sm select-none bg-white/50"
          >
            Drag blocks from the left panel to start designing
          </div>

          <!-- Block list -->
          <component
            v-for="(block, index) in editorStore.blocks"
            :key="block.id"
            :is="blockComponent(block.type)"
            :block="block"
            :index="index"
          />
        </div>
      </main>

      <!-- Right: Inspector -->
      <Inspector />

    </div>
  </div>

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
import { Button, TextInput } from "frappe-ui";
import { useEditorStore } from "../stores/editor";
import Inspector from "../components/Inspector.vue";
import LayersPanel from "../components/LayersPanel.vue";
import SendModal from "../components/SendModal.vue";

const editorStore = useEditorStore();
const leftTab    = ref("Blocks");
const saving     = ref(false);
const previewing = ref(false);
const showSendModal = ref(false);
const saveMsg    = ref("");
const errorMsg   = ref("");
const subject    = ref("");
const previewText = ref("");

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

// ── Block palette ─────────────────────────────────────────────────────────────
const availableBlocks = [
  { type: "hero",       label: "Hero",         icon: "◉" },
  { type: "text",       label: "Text",         icon: "¶" },
  { type: "image_text", label: "Image + Text", icon: "▣" },
  { type: "button",     label: "Button",       icon: "▷" },
  { type: "divider",    label: "Divider",      icon: "—" },
  { type: "footer",     label: "Footer",       icon: "≡" },
];

const blockComponentCache = {};
function blockComponent(type) {
  if (!blockComponentCache[type]) {
    blockComponentCache[type] = defineAsyncComponent(
      () => import(`../components/blocks/${type}.vue`)
    );
  }
  return blockComponentCache[type];
}

let dragging = null;
function onDragStart(block) { dragging = block; }
function onDrop() {
  if (dragging) {
    editorStore.addBlock(dragging.type);
    dragging = null;
  }
}
</script>
