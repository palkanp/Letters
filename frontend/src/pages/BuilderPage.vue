<template>
  <div class="letters-builder flex flex-col bg-surface-gray-1 font-sans overflow-hidden" style="height: 100vh">

    <!-- ── Top bar ─────────────────────────────────────────────────────────── -->
    <header class="flex-shrink-0 h-12 bg-white border-b border-outline-gray-1 flex items-center px-4 gap-3">

      <!-- Brand + page menu (Frappe Builder-style left dropdown) -->
      <Dropdown :options="menuOptions" placement="bottom-start">
        <template #default="{ open }">
          <button
            type="button"
            class="flex-shrink-0 flex items-center gap-1 h-8 pl-1.5 pr-1 rounded-md hover:bg-surface-gray-2 transition-colors"
            aria-label="Campaign menu"
          >
            <span class="w-6 h-6 rounded-md bg-gray-900 text-white flex items-center justify-center text-xs font-bold">L</span>
            <FeatherIcon :name="open ? 'chevron-up' : 'chevron-down'" class="w-3.5 h-3.5 text-ink-gray-4" />
          </button>
        </template>
      </Dropdown>

      <div class="w-px h-4 bg-outline-gray-2 mx-0.5" />

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
          class="flex items-center gap-1.5 min-w-0 max-w-sm px-2 py-1 rounded-md hover:bg-surface-gray-2 transition-colors group"
          title="Campaign settings"
          @click="showSettings = true"
        >
          <span class="truncate text-sm font-medium text-ink-gray-8">
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

        <div class="w-px h-4 bg-outline-gray-2 mx-0.5" />

        <!-- Sending: inline progress bar -->
        <template v-if="campaignStatus === 'Sending'">
          <div class="flex items-center gap-2 min-w-[180px]">
            <Progress
              :value="sendProgress.total ? Math.round(sendProgress.sent / sendProgress.total * 100) : 5"
              size="md"
              class="flex-1"
            />
            <span class="text-xs tabular-nums text-ink-gray-5 flex-shrink-0">{{ sendProgress.sent }}/{{ sendProgress.total }}</span>
          </div>
        </template>

        <!-- Sent / Failed / Partial: status badge only -->
        <template v-else-if="campaignStatus === 'Sent' || campaignStatus === 'Partial' || campaignStatus === 'Failed'">
          <Badge
            :theme="campaignStatus === 'Sent' ? 'green' : campaignStatus === 'Partial' ? 'orange' : 'red'"
            variant="subtle"
            size="md"
          >
            <template #prefix>
              <FeatherIcon :name="campaignStatus === 'Sent' ? 'check-circle' : 'alert-circle'" class="w-3 h-3" />
            </template>
            {{ campaignStatus === 'Sent' ? 'Sent' : campaignStatus === 'Partial' ? 'Partially sent' : 'Failed' }}
          </Badge>
        </template>

        <!-- Scheduled: status badge with time -->
        <template v-else-if="campaignStatus === 'Scheduled'">
          <Badge theme="blue" variant="subtle" size="md">
            <template #prefix><FeatherIcon name="clock" class="w-3 h-3" /></template>
            Scheduled{{ editorStore.campaignDoc?.scheduled_at ? ` · ${formatScheduledAt(editorStore.campaignDoc.scheduled_at)}` : '' }}
          </Badge>
        </template>

        <!-- Draft: normal preview + send -->
        <template v-else>
          <Dropdown :options="previewOptions" placement="bottom-end">
            <template #default="{ open }">
              <Button variant="ghost" size="sm">
                Preview
                <template #suffix><FeatherIcon :name="open ? 'chevron-up' : 'chevron-down'" class="w-3 h-3" /></template>
              </Button>
            </template>
          </Dropdown>
          <Dropdown :options="sendOptions" placement="bottom-end">
            <template #default="{ open }">
              <Button variant="solid" size="sm" :disabled="!editorStore.campaignDoc">
                Send
                <template #suffix><FeatherIcon :name="open ? 'chevron-up' : 'chevron-down'" class="w-3 h-3" /></template>
              </Button>
            </template>
          </Dropdown>
        </template>
      </div>
    </header>

    <!-- ── Body ──────────────────────────────────────────────────────────────── -->
    <div class="flex flex-1 overflow-hidden">

      <!-- Permanent left sidebar: Layers + Add block -->
      <aside
        class="flex-shrink-0 bg-white border-r border-outline-gray-1 flex flex-col relative"
        :style="{ width: leftPanelWidth + 'px' }"
      >
        <!-- Drag handle (right edge) -->
        <div
          class="absolute top-0 right-0 h-full w-1 cursor-col-resize hover:bg-blue-400 opacity-0 hover:opacity-100 z-[1] transition-opacity"
          @mousedown="startLeftResize"
        />
        <!-- Header -->
        <div class="flex items-center justify-between px-4 py-3.5 border-b border-outline-gray-1 flex-shrink-0">
          <template v-if="pickerTarget !== null">
            <span class="text-xs font-semibold text-ink-gray-4 uppercase tracking-widest">Add Block</span>
            <button type="button" class="text-ink-gray-4 hover:text-ink-gray-7 transition-colors" @click="closePicker">
              <FeatherIcon name="x" class="w-3.5 h-3.5" />
            </button>
          </template>
          <template v-else>
            <span class="text-xs font-semibold text-ink-gray-4 uppercase tracking-widest">Layers</span>
            <span class="text-xs text-ink-gray-3 tabular-nums">{{ editorStore.blocks.length }}</span>
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
          <div class="bg-surface-white border border-outline-gray-2 rounded-xl shadow-2xl overflow-hidden" style="width:360px">
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
        class="flex-1 overflow-y-auto p-6 relative bg-gray-100"
        @dragover.prevent
        @drop="onCanvasDrop"
        @click="editorStore.selectBlock(null)"
      >
        <!-- Zoom controls -->
        <div class="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-1 bg-surface-white border border-outline-gray-2 rounded-lg shadow-sm px-1 py-1 z-10">
          <button type="button" class="w-6 h-6 flex items-center justify-center rounded text-ink-gray-5 hover:bg-surface-gray-2 text-sm leading-none" @click.stop="stepZoom(-1)">−</button>
          <button type="button" class="min-w-[3rem] text-xs text-ink-gray-6 hover:bg-surface-gray-2 rounded px-1 py-0.5 tabular-nums" @click.stop="canvasZoom = 1">{{ Math.round(canvasZoom * 100) }}%</button>
          <button type="button" class="w-6 h-6 flex items-center justify-center rounded text-ink-gray-5 hover:bg-surface-gray-2 text-sm leading-none" @click.stop="stepZoom(1)">+</button>
        </div>

        <div
          class="mx-auto bg-white origin-top transition-transform shadow-sm"
          :style="{ maxWidth: editorStore.emailWidth + 'px', minHeight: '200px', transform: `scale(${canvasZoom})`, transformOrigin: 'top center', marginBottom: canvasZoom < 1 ? `calc((${canvasZoom} - 1) * 100%)` : undefined, color: '#374151', colorScheme: 'light' }"
        >

          <!-- Loading skeleton (while fetching a saved campaign) -->
          <div v-if="loadingCampaign" class="p-6 space-y-3" aria-busy="true" aria-label="Loading campaign">
            <div v-for="n in 4" :key="n" class="h-16 bg-surface-gray-2 animate-pulse rounded-lg" />
          </div>

          <!-- Empty state (not loading, no blocks) -->
          <div
            v-else-if="!editorStore.blocks.length"
            class="border-2 border-dashed border-outline-gray-2 rounded-xl p-16 text-center bg-surface-white/50 select-none"
          >
            <div class="mb-3 opacity-40"><FeatherIcon name="inbox" class="w-10 h-10 mx-auto text-ink-gray-4" /></div>
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

  <!-- Keyboard shortcuts viewer -->
  <Dialog
    :model-value="showShortcuts"
    title="Keyboard Shortcuts"
    size="sm"
    @update:model-value="(v) => { if (!v) showShortcuts = false }"
  >
    <template #default>
      <div class="space-y-1 text-sm">
        <div v-for="s in SHORTCUTS" :key="s.label" class="flex items-center justify-between py-1.5 border-b border-outline-gray-1 last:border-0">
          <span class="text-ink-gray-7">{{ s.label }}</span>
          <div class="flex items-center gap-1">
            <kbd v-for="k in s.keys" :key="k" class="inline-flex items-center px-1.5 py-0.5 rounded bg-surface-gray-2 border border-outline-gray-2 text-xs font-mono text-ink-gray-6">{{ k }}</kbd>
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end w-full">
        <Button @click="showShortcuts = false">Close</Button>
      </div>
    </template>
  </Dialog>

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

  <!-- Broken link checker dialog -->
  <Dialog
    :model-value="showLinkChecker"
    title="Link Checker"
    size="md"
    @update:model-value="(v) => { if (!v) showLinkChecker.value = false; }"
  >
    <template #default>
      <!-- Loading state -->
      <div v-if="checkingLinks" class="py-8 flex flex-col items-center gap-3">
        <FeatherIcon name="loader" class="w-6 h-6 text-ink-gray-4 animate-spin" />
        <span class="text-sm text-ink-gray-5">Checking all links…</span>
      </div>

      <!-- Empty state -->
      <div v-else-if="!linkResults.length" class="py-8 flex flex-col items-center gap-2">
        <FeatherIcon name="link" class="w-6 h-6 text-ink-gray-3" />
        <p class="text-sm text-ink-gray-5">No links found in this email.</p>
      </div>

      <!-- Results -->
      <div v-else class="flex flex-col gap-1">
        <!-- Summary row -->
        <div class="flex items-center gap-2 pb-2 mb-1 border-b border-outline-gray-1">
          <Badge v-if="linkResults.filter(r => r.status === 'ok').length" theme="green" variant="subtle" size="sm">
            <template #prefix><FeatherIcon name="check" class="w-3 h-3" /></template>
            {{ linkResults.filter(r => r.status === 'ok').length }} working
          </Badge>
          <Badge v-if="linkResults.filter(r => r.status === 'error').length" theme="red" variant="subtle" size="sm">
            <template #prefix><FeatherIcon name="alert-circle" class="w-3 h-3" /></template>
            {{ linkResults.filter(r => r.status === 'error').length }} broken
          </Badge>
          <Badge v-if="linkResults.filter(r => r.status === 'skipped').length" theme="gray" variant="subtle" size="sm">
            {{ linkResults.filter(r => r.status === 'skipped').length }} skipped
          </Badge>
          <Button class="ml-auto" size="xs" variant="ghost" icon-left="refresh-cw" :loading="checkingLinks" @click="openLinkChecker">Re-check</Button>
        </div>

        <!-- Link rows -->
        <div class="max-h-80 overflow-y-auto flex flex-col gap-1">
          <div
            v-for="r in linkResults"
            :key="r.url"
            class="rounded border px-3 py-2.5"
            :class="{
              'border-outline-gray-1 bg-surface-gray-1': r.status === 'ok' || r.status === 'skipped',
              'border-outline-red-2 bg-surface-red-1': r.status === 'error',
            }"
          >
            <!-- Top row: url + badge -->
            <div class="flex items-center gap-2 min-w-0">
              <FeatherIcon
                :name="r.status === 'ok' ? 'check-circle' : r.status === 'skipped' ? 'minus' : 'alert-circle'"
                class="w-3.5 h-3.5 flex-shrink-0"
                :class="r.status === 'ok' ? 'text-green-500' : r.status === 'skipped' ? 'text-ink-gray-3' : 'text-red-500'"
              />
              <span class="text-xs font-mono text-ink-gray-7 truncate flex-1 min-w-0">{{ r.url }}</span>
              <Badge
                :theme="r.status === 'ok' ? 'green' : r.status === 'skipped' ? 'gray' : 'red'"
                variant="subtle"
                size="sm"
                class="flex-shrink-0"
              >{{ r.status === 'ok' ? (r.code || 'OK') : r.status === 'skipped' ? 'Non-HTTP' : r.code ? `${r.code}` : 'Unreachable' }}</Badge>
            </div>

            <!-- Inline fix for broken links -->
            <div v-if="r.status === 'error'" class="mt-2 flex items-center gap-1.5">
              <TextInput
                size="sm"
                class="flex-1 min-w-0"
                placeholder="Replace with correct URL…"
                :modelValue="r._fix || ''"
                @update:modelValue="(v) => r._fix = v"
                @keyup.enter="applyLinkFix(r)"
              />
              <Button size="sm" variant="solid" :disabled="!r._fix" @click="applyLinkFix(r)">Fix</Button>
            </div>
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end w-full">
        <Button @click="showLinkChecker.value = false">Close</Button>
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
      <div class="flex gap-2">
        <DatePicker
          v-model="scheduleDate"
          placeholder="Pick a date"
          :min="minScheduleDate"
          class="flex-1"
        />
        <TimePicker
          v-model="scheduleTime"
          placeholder="Pick a time"
          class="flex-1"
        />
      </div>
      <p v-if="scheduleDate && scheduleTime" class="mt-2 text-xs text-ink-gray-5">
        Sending on {{ scheduleDate }} at {{ scheduleTime }}
      </p>
    </template>
    <template #actions>
      <div class="flex items-center justify-end gap-2 w-full">
        <Button @click="showScheduleModal = false">Cancel</Button>
        <Button
          variant="solid"
          :loading="scheduling"
          :disabled="!scheduleDate || !scheduleTime || scheduling"
          @click="scheduleCampaign"
        >Schedule</Button>
      </div>
    </template>
  </Dialog>

</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, provide, nextTick } from "vue";
import { Button, TextInput, FeatherIcon, Dialog, Dropdown, Tooltip, toast, Progress, Badge, DatePicker, TimePicker } from "frappe-ui";
import { useDark, useToggle } from "@vueuse/core";
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
const isDark = useDark({ attribute: "data-theme", valueDark: "dark", valueLight: "light" });
const toggleDark = useToggle(isDark);
const showShortcuts = ref(false);

const SHORTCUTS = [
  { label: "Undo",             keys: ["⌘", "Z"] },
  { label: "Redo",             keys: ["⌘", "⇧", "Z"] },
  { label: "Save",             keys: ["⌘", "S"] },
  { label: "Duplicate block",  keys: ["⌘", "D"] },
  { label: "Delete block",     keys: ["⌫"] },
  { label: "Deselect",         keys: ["Esc"] },
  { label: "Preview",          keys: ["⌘", "⇧", "P"] },
  { label: "Zoom in",          keys: ["⌘", "+"] },
  { label: "Zoom out",         keys: ["⌘", "−"] },
  { label: "Reset zoom",       keys: ["⌘", "0"] },
];

const canvasZoom = ref(1);
const ZOOM_LEVELS = [0.5, 0.67, 0.75, 0.9, 1, 1.1, 1.25, 1.5];

function stepZoom(dir) {
  const idx = ZOOM_LEVELS.findIndex(z => z >= canvasZoom.value - 0.01);
  const next = dir > 0
    ? ZOOM_LEVELS[Math.min(idx + 1, ZOOM_LEVELS.length - 1)]
    : ZOOM_LEVELS[Math.max(idx - 1, 0)];
  canvasZoom.value = next ?? canvasZoom.value;
}
const previewing    = ref(false);
const loadingCampaign = ref(false);
const showSettings = ref(false);
const showTemplateLibrary = ref(false);
const sendProgress = ref({ status: "Queued", sent: 0, total: 0 });
let _progressTimer = null;
const campaignStatus = computed(() => {
  // While actively polling use live sendProgress status, otherwise use campaignDoc
  if (["Sending", "Queued"].includes(sendProgress.value.status) && _progressTimer) {
    return "Sending";
  }
  return editorStore.campaignDoc?.status || null;
});
const showLinkChecker = ref(false);
const linkResults = ref([]);
const checkingLinks = ref(false);

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
      {
        label: "Keyboard Shortcuts",
        icon: "command",
        onClick: () => (showShortcuts.value = true),
      },
      {
        label: isDark.value ? "Switch to Light Mode" : "Switch to Dark Mode",
        icon: isDark.value ? "sun" : "moon",
        onClick: () => toggleDark(),
      },
    ],
  },
]);
const previewOptions = computed(() => [
  { label: "Preview", icon: "external-link", onClick: openPreview },
  { label: "Send test email", icon: "send", onClick: openTestModal },
  { label: "Test broken links", icon: "link", onClick: openLinkChecker },
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
const scheduleDate = ref("");
const scheduleTime = ref("");
const scheduling = ref(false);
const minScheduleDate = computed(() => {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
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
  // Non-modifier shortcuts (only when not in a text field)
  if (!e.metaKey && !e.ctrlKey) {
    const inInput = document.activeElement?.isContentEditable ||
      ["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName);
    if (!inInput) {
      if (e.key === "Escape") {
        editorStore.selectBlock(null);
        return;
      }
      if ((e.key === "Delete" || e.key === "Backspace") && editorStore.selectedBlockId) {
        e.preventDefault();
        editorStore.removeBlock(editorStore.selectedBlockId);
        return;
      }
    }
    return;
  }
  const mod = true;
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
    clearTimeout(_autoSaveTimer);
    saveCampaign();
    return;
  }
  // Duplicate selected block: Cmd/Ctrl + D
  if (e.key === "d") {
    if (document.activeElement?.isContentEditable) return;
    if (["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName)) return;
    e.preventDefault();
    if (editorStore.selectedBlockId) editorStore.duplicateBlock(editorStore.selectedBlockId);
    return;
  }
  // Preview: Cmd/Ctrl + Shift + P
  if (e.key === "p" && e.shiftKey) {
    e.preventDefault();
    openPreview();
    return;
  }
  // Zoom in: Cmd/Ctrl + =  or  +
  if (e.key === "=" || e.key === "+") {
    e.preventDefault();
    stepZoom(1);
    return;
  }
  // Zoom out: Cmd/Ctrl + -
  if (e.key === "-") {
    e.preventDefault();
    stepZoom(-1);
    return;
  }
  // Reset zoom: Cmd/Ctrl + 0
  if (e.key === "0") {
    e.preventDefault();
    canvasZoom.value = 1;
    return;
  }
}

onMounted(() => {
  window.addEventListener("beforeunload", beforeUnloadHandler);
  window.addEventListener("keydown", keydownHandler);
});
onUnmounted(() => {
  window.removeEventListener("beforeunload", beforeUnloadHandler);
  window.removeEventListener("keydown", keydownHandler);
  clearInterval(_progressTimer);
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
function formatScheduledAt(s) {
  try { return new Date(s.replace(" ", "T")).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }); }
  catch { return s; }
}

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
        email_width:  editorStore.emailWidth,
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
        email_width:  editorStore.emailWidth,
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
    showSettings.value = true;
    toast.warning("Add a subject line before sending.");
    return;
  }
  if (!editorStore.blocks.length) {
    toast.warning("Your canvas is empty. Add some blocks before sending.");
    return;
  }
  if (!recipientConfig.value) {
    showSettings.value = true;
    toast.warning("Choose recipients before sending.");
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
    sendProgress.value = { status: "Queued", sent: 0, total: count };
    if (editorStore.campaignDoc) editorStore.campaignDoc.status = "Sending";
    _startProgressPolling();
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

function _startProgressPolling() {
  clearInterval(_progressTimer);
  _progressTimer = setInterval(async () => {
    if (!editorStore.campaignDoc?.name) { clearInterval(_progressTimer); return; }
    try {
      const r = await frappe.call({
        method: "letters.letters.api.get_send_progress",
        args: { name: editorStore.campaignDoc.name },
      });
      sendProgress.value = r.message;
      if (["Sent", "Failed", "Partial"].includes(r.message.status)) {
        clearInterval(_progressTimer);
        _progressTimer = null;
        // Sync final status back to campaignDoc so toolbar badge reflects it
        if (editorStore.campaignDoc) editorStore.campaignDoc.status = r.message.status;
        const label = r.message.status === "Sent" ? "Campaign sent successfully!" : `Send ${r.message.status.toLowerCase()}.`;
        toast[r.message.status === "Sent" ? "success" : "warning"](label);
      }
    } catch { clearInterval(_progressTimer); _progressTimer = null; }
  }, 2000);
}

async function openLinkChecker() {
  if (!editorStore.blocks.length) {
    toast.warning("Canvas is empty. Add some blocks first.");
    return;
  }
  showLinkChecker.value = true;
  checkingLinks.value = true;
  linkResults.value = [];
  try {
    const args = editorStore.campaignDoc?.name
      ? { name: editorStore.campaignDoc.name }
      : { blocks: JSON.stringify(editorStore.blocks.map(stripIds)) };
    const res = await frappe.call({ method: "letters.letters.api.check_links", args });
    linkResults.value = res.message || [];
  } catch (e) {
    toast.error("Link check failed: " + describeError(e));
    showLinkChecker.value = false;
  } finally {
    checkingLinks.value = false;
  }
}

function applyLinkFix(result) {
  const oldUrl = result.url;
  const newUrl = (result._fix || "").trim();
  if (!newUrl || newUrl === oldUrl) return;

  function fixInBlock(block) {
    if (!block) return;
    if (block.props) {
      for (const key of Object.keys(block.props)) {
        if (typeof block.props[key] === "string" && block.props[key].includes(oldUrl)) {
          block.props[key] = block.props[key].replaceAll(oldUrl, newUrl);
        }
      }
    }
    // container children
    if (Array.isArray(block.children)) block.children.forEach(fixInBlock);
    // columns block: each column has a .blocks array
    if (Array.isArray(block.columns)) {
      block.columns.forEach(col => {
        if (Array.isArray(col.blocks)) col.blocks.forEach(fixInBlock);
      });
    }
  }

  editorStore.blocks.forEach(fixInBlock);
  editorStore.markDirty();

  // Flip the row to green in the dialog
  result.url = newUrl;
  result.status = "ok";
  result.code = null;
  result._fix = "";
  toast.success("Link updated — press ⌘S to save.");
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
  if (!scheduleDate.value || !scheduleTime.value) return;
  scheduling.value = true;
  try {
    // Combine date (YYYY-MM-DD) + time (HH:mm or HH:mm:ss) into local datetime
    // string — Frappe server works in local time so no UTC conversion needed.
    const dt = `${scheduleDate.value} ${scheduleTime.value}`;
    await frappe.call({
      method: "letters.letters.api.schedule_campaign",
      args: { name: editorStore.campaignDoc.name, scheduled_at: dt },
    });
    toast.success(`Scheduled for ${scheduleDate.value} at ${scheduleTime.value}`);
    showScheduleModal.value = false;
    scheduleDate.value = "";
    scheduleTime.value = "";
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
  const id = editorStore.selectedBlockId;
  if (!id) return;
  setTimeout(() => {
    const el = document.querySelector(`[data-block-id="${id}"]`);
    el?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, 50);
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
