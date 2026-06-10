<template>
  <div class="letters-builder flex flex-col bg-gray-100 font-sans overflow-hidden" style="height: 100vh">

    <!-- ── Top bar ─────────────────────────────────────────────────────────── -->
    <header class="flex-shrink-0 h-12 bg-white border-b border-gray-200 flex items-center px-4 gap-3">

      <!-- Back to campaigns list -->
      <a
        href="/app/letters-campaign"
        title="Back to campaigns"
        aria-label="Back to campaigns"
        class="flex-shrink-0 flex items-center justify-center w-7 h-7 rounded-md text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors"
      ><FeatherIcon name="arrow-left" class="w-4 h-4" /></a>

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

      <!-- Actions -->
      <div class="flex items-center gap-1.5 flex-shrink-0">
        <!-- Undo / Redo -->
        <button
          type="button"
          class="w-7 h-7 flex items-center justify-center rounded-md text-gray-400 transition-colors"
          :class="editorStore.canUndo ? 'hover:text-gray-700 hover:bg-gray-100' : 'opacity-30 cursor-not-allowed'"
          :disabled="!editorStore.canUndo"
          title="Undo (⌘Z)"
          @click="editorStore.undo()"
        ><FeatherIcon name="corner-up-left" class="w-3.5 h-3.5" /></button>
        <button
          type="button"
          class="w-7 h-7 flex items-center justify-center rounded-md text-gray-400 transition-colors"
          :class="editorStore.canRedo ? 'hover:text-gray-700 hover:bg-gray-100' : 'opacity-30 cursor-not-allowed'"
          :disabled="!editorStore.canRedo"
          title="Redo (⌘⇧Z)"
          @click="editorStore.redo()"
        ><FeatherIcon name="corner-up-right" class="w-3.5 h-3.5" /></button>

        <div class="w-px h-4 bg-gray-200 mx-0.5" />

        <Button variant="ghost" size="sm" title="Template Library" @click="showTemplateLibrary = true">
          <template #prefix><FeatherIcon name="grid" class="w-3.5 h-3.5" /></template>
          Templates
        </Button>
        <Button variant="ghost" size="sm" :loading="previewing" title="Preview in new window" aria-label="Preview in new tab" @click="openPreview">
          <template #prefix><FeatherIcon name="external-link" class="w-3.5 h-3.5" /></template>
          Preview
        </Button>
        <Button variant="ghost" size="sm" :loading="saving" :title="editorStore.isDirty ? 'Unsaved changes' : 'Up to date'" @click="saveCampaign">
          <template #prefix>
            <span class="relative">
              <FeatherIcon name="upload-cloud" class="w-3.5 h-3.5" />
              <span v-if="editorStore.isDirty" class="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 bg-orange-400 rounded-full" />
            </span>
          </template>
          Save
        </Button>
        <Button variant="ghost" size="sm" :loading="duplicating" :disabled="!editorStore.campaignDoc || duplicating" title="Duplicate this campaign" @click="duplicateCampaign">
          <template #prefix><FeatherIcon name="copy" class="w-3.5 h-3.5" /></template>
          Duplicate
        </Button>

        <div class="w-px h-4 bg-gray-200 mx-0.5" />

        <!-- Recipients button — configure who to send to -->
        <Button variant="ghost" size="sm" :disabled="!editorStore.campaignDoc" @click="showRecipientsModal = true">
          <template #prefix><FeatherIcon name="users" class="w-3.5 h-3.5" /></template>
          Recipients
        </Button>
        <!-- Test send — sends to logged-in user only -->
        <Button variant="ghost" size="sm" :loading="testSending" :disabled="!editorStore.campaignDoc || testSending" title="Send a test to yourself" @click="sendTest">
          <template #prefix><FeatherIcon name="send" class="w-3.5 h-3.5" /></template>
          Test
        </Button>
        <!-- Send button — sends directly, no popup -->
        <Button variant="subtle" size="sm" :loading="sending" :disabled="!editorStore.campaignDoc || sending" @click="sendCampaign">Send</Button>
      </div>
    </header>

    <!-- ── Body ──────────────────────────────────────────────────────────────── -->
    <div class="flex flex-1 overflow-hidden">

      <!-- Permanent left sidebar: Layers + Add block -->
      <aside
        class="flex-shrink-0 bg-white border-r border-gray-200 flex flex-col relative"
        :style="{ width: leftPanelWidth + 'px' }"
      >
        <!-- Drag handle (right edge) -->
        <div
          class="absolute top-0 right-0 h-full w-1 cursor-col-resize hover:bg-blue-400 opacity-0 hover:opacity-100 z-20 transition-opacity"
          @mousedown="startLeftResize"
        />
        <!-- Header -->
        <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100 flex-shrink-0">
          <span class="text-xs font-semibold text-gray-400 uppercase tracking-widest">Layers</span>
          <span class="text-xs text-gray-300 tabular-nums">{{ editorStore.blocks.length }}</span>
        </div>

        <!-- Layer list fills remaining space -->
        <div class="flex-1 overflow-y-auto min-h-0">
          <LayersPanel />
        </div>

        <!-- Add block / Add container buttons pinned to bottom -->
        <div class="flex-shrink-0 p-3 border-t border-gray-100 flex flex-col gap-2">
          <button
            type="button"
            class="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl
                   bg-gray-900 text-white text-xs font-semibold
                   hover:bg-gray-700 transition-colors"
            @click.stop="onAddBlock"
          >
            <FeatherIcon name="plus" class="w-3.5 h-3.5" /> Add block
          </button>
          <button
            type="button"
            class="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl
                   border border-gray-200 text-gray-600 text-xs font-semibold
                   hover:bg-gray-100 hover:border-gray-300 transition-colors"
            @click.stop="addContainer"
          >
            <FeatherIcon name="box" class="w-3.5 h-3.5" /> Add container
          </button>
        </div>
      </aside>

      <!-- Canvas -->
      <main
        class="flex-1 overflow-y-auto p-6"
        @dragover.prevent
        @drop="onCanvasDrop"
        @click="editorStore.selectBlock(null)"
      >
        <div class="mx-auto bg-white shadow-sm" style="max-width:600px;min-height:200px">

          <!-- Loading skeleton (while fetching a saved campaign) -->
          <div v-if="loadingCampaign" class="p-6 space-y-3" aria-busy="true" aria-label="Loading campaign">
            <div v-for="n in 4" :key="n" class="h-16 bg-gray-100 animate-pulse rounded-lg" />
          </div>

          <!-- Empty state (not loading, no blocks) -->
          <div
            v-else-if="!editorStore.blocks.length"
            class="border-2 border-dashed border-gray-300 rounded-xl p-16 text-center text-gray-400 bg-white/50 select-none"
          >
            <div class="mb-3 opacity-40"><FeatherIcon name="inbox" class="w-10 h-10 mx-auto text-gray-400" /></div>
            <p class="text-sm font-medium mb-1">Your canvas is empty</p>
            <p class="text-xs opacity-60">Use <strong>+ Add block</strong> in the left panel to get started</p>
          </div>

          <!-- Block list with inline adders -->
          <template v-else-if="!loadingCampaign">
            <!-- Adder before first block -->
            <BlockAdderRow :after-index="-1" @open="(i) => openPicker({ mode: 'top', afterIndex: i })" />

            <template v-for="(block, index) in editorStore.blocks" :key="block.id">
              <BlockRenderer :block="block" :index="index" />
              <!-- Adder after each block -->
              <BlockAdderRow :after-index="index" @open="(i) => openPicker({ mode: 'top', afterIndex: i })" />
            </template>
          </template>
        </div>
      </main>

      <!-- Drag handle (left edge of Inspector) -->
      <div
        class="flex-shrink-0 w-1 bg-transparent hover:bg-blue-400 cursor-col-resize z-20 transition-colors"
        @mousedown="startRightResize"
      />

      <!-- Right: Inspector -->
      <Inspector :width="rightPanelWidth" />

    </div>
  </div>

  <!-- ── Block Picker overlay ───────────────────────────────────────────────── -->
  <Teleport to="body">
    <div
      v-if="pickerTarget !== null"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/25 backdrop-blur-sm"
      @click.self="closePicker"
    >
      <div class="bg-white rounded-2xl shadow-2xl border border-gray-100 p-5 w-80">
        <div class="flex items-center justify-between mb-4">
          <span class="text-xs font-semibold text-gray-400 uppercase tracking-widest">Add a block</span>
          <button
            type="button"
            class="w-6 h-6 flex items-center justify-center rounded-md text-gray-400 hover:text-gray-700 hover:bg-gray-100"
            @click="closePicker"
          ><FeatherIcon name="x" class="w-3.5 h-3.5" /></button>
        </div>
        <div class="grid grid-cols-3 gap-1.5">
          <button
            v-for="b in availableBlocks"
            :key="b.type"
            type="button"
            class="flex flex-col items-center gap-1.5 px-2 py-3 rounded-xl text-gray-600 hover:bg-gray-900 hover:text-white transition-colors group"
            @click="insertBlock(b.type)"
          >
            <FeatherIcon :name="b.icon" class="w-4 h-4" />
            <span class="text-xs font-medium leading-none">{{ b.label }}</span>
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <RecipientsModal
    v-if="showRecipientsModal"
    :campaign-name="editorStore.campaignName"
    :campaign-doc="editorStore.campaignDoc"
    @close="showRecipientsModal = false"
    @saved="onRecipientsSaved"
  />

  <TemplateLibrary
    v-if="showTemplateLibrary"
    @close="showTemplateLibrary = false"
    @apply="onTemplateApply"
  />

</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, provide } from "vue";
import { Button, TextInput, FeatherIcon, toast } from "frappe-ui";
import { useEditorStore } from "../stores/editor";
import Inspector from "../components/Inspector.vue";
import LayersPanel from "../components/LayersPanel.vue";
import RecipientsModal from "../components/RecipientsModal.vue";
import TemplateLibrary from "../components/TemplateLibrary.vue";
import BlockAdderRow from "../components/BlockAdderRow.vue";
import BlockRenderer from "../components/BlockRenderer.vue";

const editorStore = useEditorStore();
const saving        = ref(false);
const previewing    = ref(false);
const loadingCampaign = ref(false);
const showRecipientsModal = ref(false);
const showTemplateLibrary = ref(false);
const recipientConfig = ref(null); // { type, email_group | recipients | (doctype + email_field + filters) }
const sending = ref(false);
const testSending = ref(false);
const duplicating = ref(false);
const subject    = ref("");
const previewText = ref("");

// ── Panel resize ──────────────────────────────────────────────────────────────
const leftPanelWidth  = ref(208); // 52 * 4px = 208
const rightPanelWidth = ref(288); // 72 * 4px = 288
const MIN_PANEL = 160;
const MAX_PANEL = 480;

function startLeftResize(e) {
  e.preventDefault();
  const startX = e.clientX;
  const startW = leftPanelWidth.value;
  function onMove(ev) {
    leftPanelWidth.value = Math.min(MAX_PANEL, Math.max(MIN_PANEL, startW + ev.clientX - startX));
  }
  function onUp() {
    window.removeEventListener("mousemove", onMove);
    window.removeEventListener("mouseup", onUp);
  }
  window.addEventListener("mousemove", onMove);
  window.addEventListener("mouseup", onUp);
}

function startRightResize(e) {
  e.preventDefault();
  const startX = e.clientX;
  const startW = rightPanelWidth.value;
  function onMove(ev) {
    rightPanelWidth.value = Math.min(MAX_PANEL, Math.max(MIN_PANEL, startW - (ev.clientX - startX)));
  }
  function onUp() {
    window.removeEventListener("mousemove", onMove);
    window.removeEventListener("mouseup", onUp);
  }
  window.addEventListener("mousemove", onMove);
  window.addEventListener("mouseup", onUp);
}

// ── Unsaved changes protection ────────────────────────────────────────────────
function beforeUnloadHandler(e) {
  if (editorStore.isDirty) {
    e.preventDefault();
    e.returnValue = ""; // required for Chrome
  }
}

// ── Keyboard shortcuts ────────────────────────────────────────────────────────
function keydownHandler(e) {
  const mod = e.metaKey || e.ctrlKey;
  if (!mod) return;
  // Undo: Cmd/Ctrl + Z (without Shift)
  if (e.key === "z" && !e.shiftKey) {
    // Only intercept when not inside an input / contenteditable
    if (document.activeElement?.isContentEditable) return;
    if (["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName)) return;
    e.preventDefault();
    editorStore.undo();
    return;
  }
  // Redo: Cmd/Ctrl + Shift + Z  or  Ctrl + Y
  if ((e.key === "z" && e.shiftKey) || (e.key === "y" && !e.shiftKey)) {
    if (document.activeElement?.isContentEditable) return;
    if (["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName)) return;
    e.preventDefault();
    editorStore.redo();
    return;
  }
  // Save: Cmd/Ctrl + S
  if (e.key === "s") {
    e.preventDefault();
    saveCampaign();
  }
}

onMounted(() => {
  window.addEventListener("beforeunload", beforeUnloadHandler);
  window.addEventListener("keydown", keydownHandler);
});
onUnmounted(() => {
  window.removeEventListener("beforeunload", beforeUnloadHandler);
  window.removeEventListener("keydown", keydownHandler);
});

// Track subject/previewText/campaignName changes as dirty.
// _suppressDirty is a counter (not a boolean) so concurrent loadCampaign
// calls each hold their own increment and don't accidentally re-enable
// dirty tracking while another load is still in flight.
let _suppressDirty = 0;
watch([subject, previewText, () => editorStore.campaignName], () => {
  if (_suppressDirty === 0) editorStore.markDirty();
});

// pickerTarget: null = closed
//   { mode: 'top', afterIndex: N }      — add to top-level canvas
//   { mode: 'child', parentId: X, afterIndex: N } — add inside a container
const pickerTarget = ref(null);

// Provide openPicker so container blocks (and any nested component) can call it
function openPicker(target) {
  if (typeof target === "number") {
    // legacy: called with just an afterIndex number (from BlockAdderRow)
    pickerTarget.value = { mode: "top", afterIndex: target };
  } else {
    // called from container with { parentId, afterIndex }
    pickerTarget.value = { mode: "child", ...target };
  }
}
provide("openPicker", openPicker);

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
  loadingCampaign.value = true;
  _suppressDirty++;
  try {
    const res = await frappe.call({ method: "letters.letters.api.get_campaign", args: { name } });
    const doc = res.message;
    editorStore.loadFromDoc(doc);
    subject.value     = doc.subject || "";
    previewText.value = doc.preview_text || "";
    document.title = (doc.title || "Untitled Campaign") + " — Letters";
    // Allow one Vue flush cycle before re-enabling dirty tracking
    await Promise.resolve();
  } catch (e) {
    toast.error("Couldn't load campaign: " + describeError(e));
  } finally {
    // Always decrement, even on error, so the watcher is never permanently silenced
    _suppressDirty--;
    loadingCampaign.value = false;
  }
}

// ── Save ──────────────────────────────────────────────────────────────────────
async function saveCampaign() {
  saving.value = true;
  try {
    const res = await frappe.call({
      method: "letters.letters.api.save_campaign",
      args: {
        name:         editorStore.campaignDoc?.name || null,
        title:        editorStore.campaignName || "Untitled Campaign",
        subject:      subject.value,
        preview_text: previewText.value,
        blocks:       JSON.stringify(editorStore.blocks.map(stripIds)),
      },
    });
    const saved = res.message;
    const isNew = !editorStore.campaignDoc;
    // Always replace the full doc object so status/title stay consistent
    editorStore.campaignDoc = saved;
    if (isNew) {
      const url = new URL(window.location.href);
      url.searchParams.set("name", saved.name);
      window.history.replaceState({}, "", url.toString());
    }
    editorStore.clearDirty();
    // Keep browser tab title in sync with the campaign name
    document.title = (editorStore.campaignName || "Untitled Campaign") + " — Letters";
    toast.success("Saved!");
  } catch (e) {
    toast.error("Couldn't save: " + describeError(e));
  } finally {
    saving.value = false;
  }
}

// ── Preview ───────────────────────────────────────────────────────────────────
async function openPreview() {
  // Open the window BEFORE the async call — browsers only allow window.open
  // inside a synchronous user-gesture handler. Opening it after an await
  // makes the popup blocker kill it silently.
  const win = window.open("", "_blank");
  if (!win) {
    toast.warning("Pop-up blocked — allow pop-ups for this site to use Preview.");
    return;
  }

  // Show a loading indicator in the new tab while we fetch the HTML.
  win.document.write(
    "<!doctype html><html><head><title>Loading preview…</title>" +
    "<style>body{font-family:system-ui,sans-serif;display:flex;align-items:center;" +
    "justify-content:center;height:100vh;margin:0;color:#6b7280;font-size:14px;}" +
    "</style></head><body>Generating preview…</body></html>"
  );
  win.document.close();

  previewing.value = true;
  try {
    const res = await frappe.call({
      method: "letters.letters.api.render_preview",
      args: {
        blocks:       JSON.stringify(editorStore.blocks.map(stripIds)),
        preview_text: previewText.value,
      },
    });
    const html          = res.message.html;
    const rawTitle      = editorStore.campaignName || "Email Preview";
    const campaignTitle = rawTitle
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");

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
    win.document.open();
    win.document.write(fullHtml);
    win.document.close();
    win.document.title = rawTitle + " — Preview";
  } catch (e) {
    win.close();
    toast.error("Preview failed: " + describeError(e));
  } finally {
    previewing.value = false;
  }
}

// ── Send ──────────────────────────────────────────────────────────────────────
async function sendCampaign() {
  if (!subject.value?.trim()) {
    toast.warning("Add a subject line before sending.");
    return;
  }
  if (!editorStore.blocks.length) {
    toast.warning("Your canvas is empty. Add some blocks before sending.");
    return;
  }
  if (!recipientConfig.value) {
    toast.warning("Select recipients first using the Recipients button.");
    return;
  }

  sending.value = true;
  try {
    const cfg  = recipientConfig.value;
    const args = { name: editorStore.campaignDoc?.name };
    if (cfg.type === "group") {
      args.email_group = cfg.email_group;
    } else if (cfg.type === "paste") {
      args.recipients = JSON.stringify(cfg.recipients);
    } else if (cfg.type === "doctype") {
      args.doctype_config = JSON.stringify({
        doctype:     cfg.doctype,
        email_field: cfg.email_field,
        filters:     cfg.filters || {},
      });
    }
    const res = await frappe.call({ method: "letters.letters.api.send_campaign", args });
    toast.success(`Queued for ${res.message.count} recipient${res.message.count === 1 ? "" : "s"}!`);
  } catch (e) {
    const raw = e?._server_messages;
    let msg = e?.message || "Send failed. Check your outgoing mail settings.";
    if (raw) {
      try { msg = JSON.parse(JSON.parse(raw)[0]).message || msg; } catch { /* keep */ }
    }
    toast.error(msg);
  } finally {
    sending.value = false;
  }
}

function onRecipientsSaved(config) {
  recipientConfig.value = config;
  showRecipientsModal.value = false;
}

// ── Duplicate ─────────────────────────────────────────────────────────────────
async function duplicateCampaign() {
  if (!editorStore.campaignDoc?.name) return;
  duplicating.value = true;
  try {
    const res = await frappe.call({
      method: "letters.letters.api.duplicate_campaign",
      args: { name: editorStore.campaignDoc.name },
    });
    const newName = res.message.name;
    toast.success(`Duplicated as "${res.message.title}" — opening it now.`);
    // Navigate to the new campaign in the same tab
    window.location.href = `/app/letters-builder?name=${encodeURIComponent(newName)}`;
  } catch (e) {
    toast.error("Duplicate failed: " + describeError(e));
    duplicating.value = false;
  }
}

// ── Test send ─────────────────────────────────────────────────────────────────
async function sendTest() {
  if (!editorStore.blocks.length) {
    toast.warning("Canvas is empty — add some blocks first.");
    return;
  }
  testSending.value = true;
  try {
    const res = await frappe.call({
      method: "letters.letters.api.send_test",
      args: {
        name:         editorStore.campaignDoc?.name || null,
        blocks:       editorStore.campaignDoc?.name ? null : JSON.stringify(editorStore.blocks.map(stripIds)),
        subject:      subject.value || "Test Email",
        preview_text: previewText.value,
      },
    });
    toast.success(`Test sent to ${res.message.sent_to}!`);
  } catch (e) {
    toast.error("Test send failed: " + describeError(e));
  } finally {
    testSending.value = false;
  }
}

// ── Template library ──────────────────────────────────────────────────────────
function onTemplateApply(templateBlocks) {
  editorStore.loadTemplate(templateBlocks);
  showTemplateLibrary.value = false;
  toast.success("Template applied — customize it and save when ready.");
}

// ── Block picker ──────────────────────────────────────────────────────────────
const availableBlocks = [
  { type: "header",        label: "Header",      icon: "award" },
  { type: "hero",          label: "Hero",        icon: "layout" },
  { type: "text",          label: "Text",        icon: "type" },
  { type: "rich_text",     label: "Rich Text",   icon: "edit-3" },
  { type: "image",         label: "Image",       icon: "image" },
  { type: "image_text",    label: "Image + Text", icon: "sidebar" },
  { type: "button",        label: "Button",      icon: "square" },
  { type: "columns",       label: "Columns",     icon: "columns" },
  { type: "link_list",     label: "Link List",   icon: "list" },
  { type: "quote",         label: "Quote",       icon: "message-square" },
  { type: "social",        label: "Social",      icon: "share-2" },
  { type: "product_card",  label: "Product",     icon: "shopping-bag" },
  { type: "video_thumb",   label: "Video",       icon: "play-circle" },
  { type: "spacer",        label: "Spacer",      icon: "minus" },
  { type: "section_label", label: "Label",       icon: "tag" },
  { type: "divider",       label: "Divider",     icon: "more-horizontal" },
  { type: "footer",        label: "Footer",      icon: "align-justify" },
];

// Smart "Add block": if a container is selected, add inside it; else append to canvas
function onAddBlock() {
  const sel = editorStore.selectedBlock;
  if (sel?.type === "container") {
    openPicker({ mode: "child", parentId: sel.id, afterIndex: (sel.children?.length ?? 1) - 1 });
  } else {
    openPicker({ mode: "top", afterIndex: editorStore.blocks.length - 1 });
  }
}

// Smart "Add container": if a container is selected, nest inside it; else append to canvas
function addContainer() {
  const sel = editorStore.selectedBlock;
  if (sel?.type === "container") {
    editorStore.addChildBlock(sel.id, "container", (sel.children?.length ?? 1) - 1);
  } else {
    editorStore.addBlock("container", editorStore.blocks.length - 1);
  }
}

function closePicker() {
  pickerTarget.value = null;
}
function insertBlock(type) {
  if (!pickerTarget.value) return;
  if (pickerTarget.value.mode === "column") {
    editorStore.addBlockToColumn(
      pickerTarget.value.blockId,
      pickerTarget.value.colIndex,
      type,
      pickerTarget.value.afterIndex,
    );
  } else if (pickerTarget.value.mode === "child") {
    editorStore.addChildBlock(pickerTarget.value.parentId, type, pickerTarget.value.afterIndex);
  } else {
    editorStore.addBlock(type, pickerTarget.value.afterIndex);
  }
  closePicker();
}

// ── Strip runtime IDs before saving (recursive for nested children) ──────────
function stripIds(block) {
  const { id: _id, ...rest } = block;
  if (rest.children?.length) {
    rest.children = rest.children.map(stripIds);
  }
  if (rest.columns?.length) {
    rest.columns = rest.columns.map(col => ({
      ...col,
      blocks: (col.blocks || []).map(stripIds),
    }));
  }
  return rest;
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
