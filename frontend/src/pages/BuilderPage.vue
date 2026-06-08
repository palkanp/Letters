<template>
  <div class="flex h-screen w-screen bg-gray-100 font-sans overflow-hidden">

    <!-- Left: Block Palette + Layers -->
    <aside class="w-52 flex-shrink-0 bg-gray-900 flex flex-col overflow-hidden">
      <!-- Tab bar -->
      <div class="flex border-b border-gray-700 flex-shrink-0">
        <button
          v-for="tab in ['Blocks', 'Layers']"
          :key="tab"
          type="button"
          class="flex-1 py-2.5 text-xs font-semibold transition-colors"
          :class="leftTab === tab
            ? 'text-white border-b-2 border-blue-500'
            : 'text-gray-400 hover:text-gray-200'"
          @click="leftTab = tab"
        >{{ tab }}</button>
      </div>

      <!-- Blocks tab -->
      <div v-if="leftTab === 'Blocks'" class="p-3 flex flex-col gap-1.5 overflow-y-auto">
        <div
          v-for="block in availableBlocks"
          :key="block.type"
          class="flex items-center gap-2 px-3 py-2 rounded-md bg-gray-800 text-gray-200 text-sm cursor-grab select-none hover:bg-gray-700 active:cursor-grabbing transition-colors"
          draggable="true"
          @dragstart="onDragStart(block)"
        >
          <span class="text-gray-400 text-xs">{{ block.icon }}</span>
          {{ block.label }}
        </div>
      </div>

      <!-- Layers tab -->
      <div v-else class="flex-1 overflow-hidden flex flex-col bg-white">
        <LayersPanel />
      </div>
    </aside>

    <!-- Center: Canvas -->
    <main
      class="flex-1 overflow-y-auto p-8"
      @dragover.prevent
      @drop="onDrop"
      @click="editorStore.selectBlock(null)"
    >
      <div class="max-w-2xl mx-auto">
        <!-- Top bar -->
        <div class="mb-3 flex flex-col gap-2">
          <div class="flex items-center gap-3">
            <TextInput
              v-model="editorStore.campaignName"
              placeholder="Campaign name…"
              class="flex-1"
              size="sm"
            />
            <Button variant="solid" theme="gray" size="sm" @click="saveCampaign" :loading="saving">
              Save
            </Button>
            <Button
              variant="ghost"
              size="sm"
              :loading="previewing"
              title="Open preview in new window"
              @click="openPreview"
            >↗</Button>
            <Button
              variant="solid"
              size="sm"
              :disabled="!editorStore.campaignDoc"
              @click="showSendModal = true"
            >Send</Button>
          </div>
          <div class="flex items-center gap-2">
            <TextInput
              v-model="subject"
              placeholder="Subject line…"
              class="flex-1"
              size="sm"
            />
            <TextInput
              v-model="previewText"
              placeholder="Preview text (shown in inbox)…"
              class="flex-1"
              size="sm"
            />
          </div>
        </div>

        <!-- Feedback banners -->
        <div v-if="saveMsg" class="mb-3 px-3 py-2 rounded bg-green-50 text-green-700 text-xs">
          {{ saveMsg }}
        </div>
        <div v-if="errorMsg" class="mb-3 px-3 py-2 rounded bg-red-50 text-red-700 text-xs">
          {{ errorMsg }}
        </div>

        <!-- Empty state -->
        <div
          v-if="!editorStore.blocks.length"
          class="border-2 border-dashed border-gray-300 rounded-lg p-16 text-center text-gray-400 text-sm"
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

    <!-- Right: Inspector / properties panel -->
    <Inspector />

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
const leftTab = ref("Blocks");
const saving = ref(false);
const previewing = ref(false);
const showSendModal = ref(false);
const saveMsg = ref("");
const errorMsg = ref("");
const subject = ref("");
const previewText = ref("");

// -------------------------------------------------------------------
// Error helper
// -------------------------------------------------------------------
function describeError(e) {
  try {
    const msgs = e?._server_messages;
    if (msgs) {
      const parsed = JSON.parse(msgs);
      const first = parsed[0];
      try { return JSON.parse(first).message || first; } catch { return first; }
    }
  } catch { /* fall through */ }
  return e?.message || e?.exc || "Something went wrong. Please try again.";
}

// -------------------------------------------------------------------
// Load campaign from URL ?name=xxx
// -------------------------------------------------------------------
const urlParams = new URLSearchParams(window.location.search);
const initialName = urlParams.get("name");

onMounted(async () => {
  if (initialName) await loadCampaign(initialName);
});

async function loadCampaign(name) {
  try {
    const res = await frappe.call({ method: "letters.letters.api.get_campaign", args: { name } });
    const doc = res.message;
    editorStore.loadFromDoc(doc);
    subject.value = doc.subject || "";
    previewText.value = doc.preview_text || "";
  } catch (e) {
    errorMsg.value = "Couldn't load this campaign: " + describeError(e);
  }
}

// -------------------------------------------------------------------
// Save
// -------------------------------------------------------------------
async function saveCampaign() {
  saving.value = true;
  saveMsg.value = "";
  errorMsg.value = "";
  try {
    const res = await frappe.call({
      method: "letters.letters.api.save_campaign",
      args: {
        name: editorStore.campaignDoc?.name || null,
        title: editorStore.campaignName || "Untitled Campaign",
        subject: subject.value,
        preview_text: previewText.value,
        blocks: JSON.stringify(
          editorStore.blocks.map(({ id: _id, ...rest }) => rest)
        ),
      },
    });
    const saved = res.message;
    const isNew = !editorStore.campaignDoc;
    if (isNew) {
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

// -------------------------------------------------------------------
// Preview — compile HTML and open in a new browser window
// The new window has a floating toolbar for desktop / mobile toggle.
// -------------------------------------------------------------------
async function openPreview() {
  previewing.value = true;
  errorMsg.value = "";
  try {
    const res = await frappe.call({
      method: "letters.letters.api.render_preview",
      args: {
        blocks: JSON.stringify(
          editorStore.blocks.map(({ id: _id, ...rest }) => rest)
        ),
        preview_text: previewText.value,
      },
    });
    const html = res.message.html;
    const campaignTitle = editorStore.campaignName || "Email Preview";

    // Floating desktop/mobile toolbar injected into the preview page
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
    font-size: 12px; padding: 5px 12px; border-radius: 6px;
    transition: background .15s;
  }
  #__preview-toolbar button:hover { background: #1f2937; }
  #__preview-toolbar button.active { background: #2563eb; color: #fff; }
  #__email-wrap { transition: max-width .3s; }
</style>
<div id="__preview-toolbar">
  <span>${campaignTitle}</span>
  <button class="active" onclick="setMode('desktop', this)">🖥 Desktop</button>
  <button onclick="setMode('mobile', this)">📱 Mobile (390px)</button>
</div>
<script>
  function setMode(mode, btn) {
    document.querySelectorAll('#__preview-toolbar button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.body.style.maxWidth = mode === 'mobile' ? '390px' : '';
    document.body.style.margin = mode === 'mobile' ? '0 auto' : '';
  }
<\/script>`;

    const fullHtml = html.replace("</body>", toolbar + "\n</body>");
    const win = window.open("", "_blank", "noopener");
    if (win) {
      win.document.write(fullHtml);
      win.document.close();
      win.document.title = campaignTitle + " — Preview";
    } else {
      errorMsg.value = "Pop-up blocked — please allow pop-ups for this site to use Preview.";
    }
  } catch (e) {
    errorMsg.value = "Couldn't render preview: " + describeError(e);
  } finally {
    previewing.value = false;
  }
}

// -------------------------------------------------------------------
// Send
// -------------------------------------------------------------------
function onSent() {
  showSendModal.value = false;
  saveMsg.value = "Campaign sent!";
  setTimeout(() => (saveMsg.value = ""), 3000);
}

// -------------------------------------------------------------------
// Block palette
// -------------------------------------------------------------------
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
