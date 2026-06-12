<template>
  <div class="letters-builder flex flex-col bg-gray-100 font-sans overflow-hidden" style="height: 100vh">

    <!-- ── Top bar ─────────────────────────────────────────────────────────── -->
    <header class="flex-shrink-0 h-12 bg-white border-b border-gray-200 flex items-center px-4 gap-3">

      <!-- Brand + page menu (Frappe Builder-style left dropdown) -->
      <Dropdown :options="menuOptions" placement="bottom-start">
        <template #default="{ open }">
          <button
            type="button"
            class="flex-shrink-0 flex items-center gap-1 h-8 pl-1.5 pr-1 rounded-md hover:bg-gray-100 transition-colors"
            aria-label="Campaign menu"
          >
            <span class="w-6 h-6 rounded-md bg-gray-900 text-white flex items-center justify-center text-xs font-bold">L</span>
            <FeatherIcon :name="open ? 'chevron-up' : 'chevron-down'" class="w-3.5 h-3.5 text-gray-400" />
          </button>
        </template>
      </Dropdown>

      <div class="w-px h-4 bg-gray-200 mx-0.5" />

      <!-- Add block / Add container — icon tools (Frappe Builder-style) -->
      <Tooltip text="Add block">
        <Button variant="ghost" size="sm" icon="plus" aria-label="Add block" @click.stop="onAddBlock" />
      </Tooltip>
      <Tooltip text="Add container">
        <Button variant="ghost" size="sm" icon="square" aria-label="Add container" @click.stop="addContainer" />
      </Tooltip>
      <Tooltip text="Add text">
        <Button variant="ghost" size="sm" icon="type" aria-label="Add text" @click.stop="insertBlock('text')" />
      </Tooltip>
      <Tooltip text="Add image">
        <Button variant="ghost" size="sm" icon="image" aria-label="Add image" @click.stop="insertBlock('image')" />
      </Tooltip>

      <!-- Centered campaign title — click opens settings too -->
      <div class="flex-1 flex items-center justify-center min-w-0">
        <button
          type="button"
          class="flex items-center gap-1.5 min-w-0 max-w-sm px-2 py-1 rounded-md hover:bg-gray-100 transition-colors group"
          title="Campaign settings"
          @click="showSettings = true"
        >
          <span class="truncate text-sm font-medium text-gray-800">
            {{ editorStore.campaignName || "Untitled Campaign" }}
          </span>
        </button>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-1.5 flex-shrink-0">

        <!-- Settings (gear) — opens the Campaign Settings dialog -->
        <Tooltip text="Campaign settings">
          <Button
            variant="ghost"
            size="sm"
            icon="settings"
            aria-label="Campaign settings"
            @click="showSettings = true"
          />
        </Tooltip>

        <div class="w-px h-4 bg-gray-200 mx-0.5" />

        <!-- Preview dropdown -->
        <Dropdown :options="previewOptions" placement="bottom-end">
          <template #default="{ open }">
            <Button variant="ghost" size="sm">
              Preview
              <template #suffix><FeatherIcon :name="open ? 'chevron-up' : 'chevron-down'" class="w-3 h-3" /></template>
            </Button>
          </template>
        </Dropdown>

        <!-- Send dropdown -->
        <Dropdown :options="sendOptions" placement="bottom-end">
          <template #default="{ open }">
            <Button variant="solid" size="sm" :disabled="!editorStore.campaignDoc">
              Send
              <template #suffix><FeatherIcon :name="open ? 'chevron-up' : 'chevron-down'" class="w-3 h-3" /></template>
            </Button>
          </template>
        </Dropdown>
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
          class="absolute top-0 right-0 h-full w-1 cursor-col-resize hover:bg-blue-400 opacity-0 hover:opacity-100 z-[1] transition-opacity"
          @mousedown="startLeftResize"
        />
        <!-- Header -->
        <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100 flex-shrink-0">
          <template v-if="pickerTarget !== null">
            <span class="text-xs font-semibold text-gray-400 uppercase tracking-widest">Add Block</span>
            <button type="button" class="text-gray-400 hover:text-gray-600 transition-colors" @click="closePicker">
              <FeatherIcon name="x" class="w-3.5 h-3.5" />
            </button>
          </template>
          <template v-else>
            <span class="text-xs font-semibold text-gray-400 uppercase tracking-widest">Layers</span>
            <span class="text-xs text-gray-300 tabular-nums">{{ editorStore.blocks.length }}</span>
          </template>
        </div>

        <!-- Block picker list (shown when pickerTarget is set) -->
        <div v-if="pickerTarget !== null" class="flex-1 overflow-y-auto min-h-0 py-1">
          <button
            v-for="b in availableBlocks"
            :key="b.type"
            type="button"
            class="flex items-center gap-2.5 w-full px-4 py-1.5 text-left text-ink-gray-7 hover:bg-surface-gray-2 transition-colors"
            @mouseenter="(e) => showBlockPreview(b.type, e)"
            @mouseleave="hideBlockPreview"
            @click="insertBlock(b.type)"
          >
            <FeatherIcon :name="b.icon" class="w-3.5 h-3.5 text-ink-gray-5 flex-shrink-0" />
            <span class="text-sm">{{ b.label }}</span>
          </button>
        </div>

        <!-- Layer list fills remaining space -->
        <div v-else class="flex-1 overflow-y-auto min-h-0">
          <LayersPanel />
        </div>
      </aside>

      <!-- Block hover preview panel -->
      <Teleport to="body">
        <div
          v-if="blockPreview.type"
          class="fixed z-50 pointer-events-none"
          :style="blockPreview.style"
        >
          <div class="bg-white border border-outline-gray-2 rounded-xl shadow-2xl overflow-hidden" style="width:360px">
            <div class="px-3 py-2 border-b border-outline-gray-1 bg-surface-gray-1">
              <span class="text-xs font-semibold text-ink-gray-5 uppercase tracking-widest">{{ blockPreview.label }}</span>
            </div>
            <div style="overflow:hidden;height:200px;display:flex;align-items:center;justify-content:center;">
              <div style="transform:scale(0.6);transform-origin:center center;width:600px;flex-shrink:0;">
                <BlockRenderer :block="blockPreview.block" :index="0" />
              </div>
            </div>
          </div>
        </div>
      </Teleport>

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
            <p class="text-xs opacity-60">Use <strong>+ Add block</strong> in the top bar to get started</p>
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
        class="flex-shrink-0 w-1 bg-transparent hover:bg-blue-400 cursor-col-resize z-[1] transition-colors"
        @mousedown="startRightResize"
      />

      <!-- Right: Inspector -->
      <Inspector :width="rightPanelWidth" />

    </div>
  </div>

  <CampaignSettings
    v-model="showSettings"
    :campaign-name="editorStore.campaignName"
    @update:campaign-name="(v) => (editorStore.campaignName = v)"
    v-model:subject="subject"
    v-model:preview-text="previewText"
    v-model:recipient-config="recipientConfig"
    :campaign-doc="editorStore.campaignDoc"
  />

  <TemplateLibrary
    v-if="showTemplateLibrary"
    @close="showTemplateLibrary = false"
    @apply="onTemplateApply"
  />

  <!-- Test email recipient prompt -->
  <Dialog
    :model-value="showTestModal"
    title="Send Test Email"
    message="Send a copy of this campaign so you can preview it in a real inbox."
    size="sm"
    @update:model-value="(v) => { if (!v) showTestModal = false }"
  >
    <template #default>
      <label class="block text-xs font-medium text-ink-gray-7 mb-1.5">Send to</label>
      <TextInput
        v-model="testRecipient"
        type="email"
        placeholder="name@example.com"
        @keyup.enter="sendTest"
      />
      <p class="text-xs text-ink-gray-5 mt-2">A copy with a <strong>[TEST]</strong> subject prefix is sent to this address.</p>
    </template>
    <template #actions>
      <div class="flex items-center justify-end gap-2 w-full">
        <Button @click="showTestModal = false">Cancel</Button>
        <Button
          variant="solid"
          :loading="testSending"
          :disabled="!testRecipient || testSending"
          @click="sendTest"
        >Send test</Button>
      </div>
    </template>
  </Dialog>

  <!-- Schedule sending dialog -->
  <Dialog
    :model-value="showScheduleModal"
    title="Schedule Sending"
    message="The campaign will be sent automatically at the chosen time."
    size="sm"
    @update:model-value="(v) => { if (!v) showScheduleModal = false }"
  >
    <template #default>
      <label class="block text-xs font-medium text-ink-gray-7 mb-1.5">Send at</label>
      <TextInput
        v-model="scheduleAt"
        type="datetime-local"
        :min="minScheduleAt"
      />
    </template>
    <template #actions>
      <div class="flex items-center justify-end gap-2 w-full">
        <Button @click="showScheduleModal = false">Cancel</Button>
        <Button
          variant="solid"
          :loading="scheduling"
          :disabled="!scheduleAt || scheduling"
          @click="scheduleCampaign"
        >Schedule</Button>
      </div>
    </template>
  </Dialog>

</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, provide, nextTick } from "vue";
import { Button, TextInput, FeatherIcon, Dialog, Dropdown, Tooltip, toast } from "frappe-ui";
import { useEditorStore } from "../stores/editor";
import { BLOCK_SCHEMA } from "../blockSchema";
import Inspector from "../components/Inspector.vue";
import LayersPanel from "../components/LayersPanel.vue";
import CampaignSettings from "../components/CampaignSettings.vue";
import TemplateLibrary from "../components/TemplateLibrary.vue";
import BlockAdderRow from "../components/BlockAdderRow.vue";
import BlockRenderer from "../components/BlockRenderer.vue";

const editorStore = useEditorStore();
const saving        = ref(false);
const previewing    = ref(false);
const loadingCampaign = ref(false);
const showSettings = ref(false);
const showTemplateLibrary = ref(false);

// Left brand dropdown (Frappe Builder-style): navigation + page-level actions
// that don't belong in the always-visible toolbar.
const menuOptions = computed(() => [
  {
    group: "navigate",
    hideLabel: true,
    items: [
      {
        label: "Back to Campaigns",
        icon: "arrow-left",
        onClick: () => (window.location.href = "/app/letters-campaign"),
      },
    ],
  },
  {
    group: "campaign",
    hideLabel: true,
    items: [
      {
        label: "Browse Templates",
        icon: "grid",
        onClick: () => (showTemplateLibrary.value = true),
      },
      {
        label: "Duplicate Campaign",
        icon: "copy",
        onClick: duplicateCampaign,
        disabled: !editorStore.campaignDoc || duplicating.value,
      },
      {
        label: "Campaign Settings",
        icon: "settings",
        onClick: () => (showSettings.value = true),
      },
    ],
  },
]);
const previewOptions = computed(() => [
  { label: "Preview", icon: "external-link", onClick: openPreview },
  { label: "Send test email", icon: "send", onClick: openTestModal },
]);

const sendOptions = computed(() => [
  {
    label: "Send now",
    icon: "send",
    onClick: sendCampaign,
    disabled: !editorStore.campaignDoc,
  },
  {
    label: "Schedule sending",
    icon: "clock",
    onClick: () => { showScheduleModal.value = true; },
    disabled: !editorStore.campaignDoc,
  },
]);

const recipientConfig = ref(null); // { type, email_group | recipients | (doctype + email_field + filters) }
const sending = ref(false);
const testSending = ref(false);
const showTestModal = ref(false);
const showScheduleModal = ref(false);
const scheduleAt = ref("");
const scheduling = ref(false);
const minScheduleAt = computed(() => {
  const d = new Date(Date.now() + 60_000); // at least 1 minute from now
  return d.toISOString().slice(0, 16);
});
// Prefill with the logged-in user's email when it looks like one (it's the
// most common test target); blank if the session id isn't an email.
const _sessionUser = (typeof window !== "undefined" && window.frappe?.session?.user) || "";
const testRecipient = ref(_sessionUser.includes("@") ? _sessionUser : "");
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
  // Save: Cmd/Ctrl + S (manual trigger alongside auto-save)
  if (e.key === "s") {
    e.preventDefault();
    clearTimeout(_autoSaveTimer);
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

// ── Auto-save (debounced 800ms — avoids saving on every drag pixel) ───────────
let _autoSaveTimer = null;
watch(() => editorStore.isDirty, (dirty) => {
  if (!dirty) return;
  clearTimeout(_autoSaveTimer);
  _autoSaveTimer = setTimeout(() => {
    if (editorStore.isDirty && !saving.value) saveCampaign();
  }, 800);
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
  let msg = "";
  try {
    const msgs = e?._server_messages;
    if (msgs) {
      const parsed = JSON.parse(msgs);
      const first = parsed[0];
      try { msg = JSON.parse(first).message || first; } catch { msg = first; }
    }
  } catch { /* fall through */ }
  // Deliberately never fall back to e.exc — that's a raw server traceback and
  // must not be shown to users.
  if (!msg) msg = e?.message || "Something went wrong. Please try again.";
  // Frappe messages may contain HTML; strip tags so toasts stay clean.
  return String(msg).replace(/<[^>]*>/g, "").trim() || "Something went wrong. Please try again.";
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
    document.title = (doc.title || "Untitled Campaign") + " · Letters";
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
    document.title = (editorStore.campaignName || "Untitled Campaign") + " · Letters";
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
    toast.warning("Pop-up blocked. Allow pop-ups for this site to use Preview.");
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

    // Inject before </body> when present; otherwise append so the toolbar
    // never silently vanishes if the compiled HTML lacks a body close tag.
    const fullHtml = html.includes("</body>")
      ? html.replace("</body>", toolbar + "\n</body>")
      : html + toolbar;
    win.document.open();
    win.document.write(fullHtml);
    win.document.close();
    win.document.title = rawTitle + " · Preview";
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
    toast.warning("Choose recipients first in Campaign Settings (the title at the top left).");
    showSettings.value = true;
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
    const { count, skipped_invalid } = res.message;
    let msg = `Queued for ${count} recipient${count === 1 ? "" : "s"}!`;
    if (skipped_invalid > 0) {
      msg += ` (${skipped_invalid} invalid address${skipped_invalid === 1 ? "" : "es"} skipped)`;
    }
    toast.success(msg);
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
    toast.success(`Duplicated as "${res.message.title}". Opening it now.`);
    // Navigate to the new campaign in the same tab
    window.location.href = `/app/letters-builder?name=${encodeURIComponent(newName)}`;
  } catch (e) {
    toast.error("Duplicate failed: " + describeError(e));
    duplicating.value = false;
  }
}

// ── Schedule send ─────────────────────────────────────────────────────────────
async function scheduleCampaign() {
  if (!scheduleAt.value) return;
  scheduling.value = true;
  try {
    // Convert local datetime-local value to ISO string the server understands
    const dt = new Date(scheduleAt.value).toISOString().replace("T", " ").slice(0, 19);
    await frappe.call({
      method: "letters.letters.api.schedule_campaign",
      args: { name: editorStore.campaignDoc.name, scheduled_at: dt },
    });
    toast.success(`Scheduled for ${new Date(scheduleAt.value).toLocaleString()}`);
    showScheduleModal.value = false;
    scheduleAt.value = "";
  } catch (e) {
    toast.error("Schedule failed: " + describeError(e));
  } finally {
    scheduling.value = false;
  }
}

// ── Test send ─────────────────────────────────────────────────────────────────
function openTestModal() {
  if (!editorStore.blocks.length) {
    toast.warning("Canvas is empty. Add some blocks first.");
    return;
  }
  showTestModal.value = true;
}

async function sendTest() {
  const email = testRecipient.value.trim();
  if (!email) {
    toast.warning("Enter an email address to send the test to.");
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
        recipient:    email,
      },
    });
    toast.success(`Test queued to ${res.message.sent_to}. It'll arrive shortly.`);
    showTestModal.value = false;
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
  toast.success("Template applied. Customize it and save when ready.");
}

// ── Block picker previews (SVG sketches) ──────────────────────────────────────
// ── Block picker ──────────────────────────────────────────────────────────────
const availableBlocks = [
  { type: "header",        label: "Header",      icon: "award" },
  { type: "hero",          label: "Hero",        icon: "layout" },
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
  hideBlockPreview();
}

// ── Block hover preview ───────────────────────────────────────────────────────
const blockPreview = ref({ type: null, label: null, block: null, style: {} });
let _previewTimer = null;

function showBlockPreview(type, e) {
  clearTimeout(_previewTimer);
  const schema = BLOCK_SCHEMA[type] ?? {};
  const defaults = schema.defaults ?? {};
  const previewBlock = { id: 0, type, props: JSON.parse(JSON.stringify(defaults)) };
  if (type === "columns") {
    previewBlock.props.column_count = "3";
    previewBlock.props.padding_top = 16;
    previewBlock.props.padding_bottom = 16;
    previewBlock.props.padding_left = 16;
    previewBlock.props.padding_right = 16;
    previewBlock.props.col_gap = 16;
    const dummyCopy = [
      "<strong>Design</strong><br>Build beautiful emails with a drag-and-drop editor.",
      "<strong>Personalise</strong><br>Add dynamic fields to tailor every message.",
      "<strong>Send</strong><br>Deliver to your list with one click.",
    ];
    previewBlock.columns = dummyCopy.map((html, i) => ({
      blocks: [{
        id: i + 1,
        type: "text",
        props: {
          html_content: `<p style="font-size:12px;color:#374151;line-height:1.5;margin:0;font-family:sans-serif">${html}</p>`,
          background_color: "#ffffff",
          padding_top: 12, padding_right: 10, padding_bottom: 12, padding_left: 10,
        },
      }],
    }));
  }
  if (type === "social") {
    previewBlock.props.x_url = "https://x.com";
    previewBlock.props.linkedin_url = "https://linkedin.com";
    previewBlock.props.github_url = "https://github.com";
  }
  if (type === "spacer") {
    previewBlock.props.background_color = "#f3f4f6";
    previewBlock.props.height = 80;
  }
  // Position to the right of the sidebar
  const rect = e.currentTarget.closest("aside").getBoundingClientRect();
  const top = Math.min(e.currentTarget.getBoundingClientRect().top, window.innerHeight - 320);
  blockPreview.value = {
    type,
    label: schema.label ?? type,
    block: previewBlock,
    style: { left: rect.right + 8 + "px", top: top + "px" },
  };
}

function hideBlockPreview() {
  clearTimeout(_previewTimer);
  _previewTimer = setTimeout(() => { blockPreview.value = { type: null, label: null, block: null, style: {} }; }, 80);
}
function insertBlock(type) {
  if (!pickerTarget.value) {
    editorStore.addBlock(type, editorStore.blocks.length - 1);
  } else if (pickerTarget.value.mode === "column") {
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
  scrollToSelected();
}

function scrollToSelected() {
  nextTick(() => {
    const id = editorStore.selectedBlockId;
    if (!id) return;
    const el = document.querySelector(`[data-block-id="${id}"]`);
    el?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  });
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

<style>
/* Ensure frappe-ui Dialog overlay sits above all canvas z-index layers */
.dialog-overlay {
  z-index: 9999 !important;
}

/* Placeholder text for contenteditable fields */
.editable-placeholder:empty::before {
  content: attr(data-placeholder);
  color: #d1d5db;
  pointer-events: none;
}
</style>
