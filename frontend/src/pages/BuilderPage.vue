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
      <div class="flex-1 flex items-center justify-center gap-2 min-w-0">
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
        <Transition name="fade">
          <span v-if="saving" class="text-xs text-ink-gray-4 flex-shrink-0">Saving…</span>
          <span v-else-if="savedFlash" class="text-xs text-ink-gray-4 flex-shrink-0">Saved</span>
        </Transition>
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
          <div class="bg-surface-base border border-outline-gray-2 rounded-xl shadow-2xl overflow-hidden" style="width:360px">
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
        <div
          class="mx-auto bg-white origin-top transition-transform shadow-sm letters-email-canvas"
          :style="{ maxWidth: editorStore.emailWidth + 'px', minHeight: '200px', transform: `scale(${canvasZoom})`, transformOrigin: 'top center', marginBottom: canvasZoom < 1 ? `calc((${canvasZoom} - 1) * 100%)` : undefined, color: '#374151', colorScheme: 'light' }"
        >

          <!-- Loading skeleton (while fetching a saved campaign) -->
          <div v-if="loadingCampaign" class="p-6 space-y-3" aria-busy="true" aria-label="Loading campaign">
            <div v-for="n in 4" :key="n" class="h-16 bg-surface-gray-2 animate-pulse rounded-lg" />
          </div>

          <!-- Empty state (not loading, no blocks) -->
          <div
            v-else-if="!editorStore.blocks.length"
            class="border-2 border-dashed border-outline-gray-2 rounded-xl p-16 text-center bg-surface-base/50 select-none"
          >
            <div class="mb-3 opacity-40"><FeatherIcon name="inbox" class="w-10 h-10 mx-auto text-ink-gray-4" /></div>
            <p class="text-sm font-medium mb-1">Your canvas is empty</p>
            <p class="text-xs opacity-60">Click <strong>+</strong> in the toolbar to add your first block</p>
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

        <!-- Zoom indicator — sticky to the viewport bottom, only visible briefly
             after a zoom change. Frappe Builder style: % on the left, a reset
             button on the right. -->
        <div class="sticky bottom-0 z-20 flex justify-center pointer-events-none pb-4 pt-4">
          <Transition name="fade">
            <div
              v-show="zoomVisible"
              class="pointer-events-auto flex items-center gap-2 bg-gray-900 text-white rounded-full shadow-lg pl-3.5 pr-1.5 py-1"
              @mouseenter="zoomVisible = true"
            >
              <span class="text-xs font-medium tabular-nums select-none">{{ Math.round(canvasZoom * 100) }}%</span>
              <button
                type="button"
                class="w-6 h-6 flex items-center justify-center rounded-full hover:bg-white/15 transition-colors"
                title="Reset to 100%"
                @click.stop="resetZoom"
              >
                <FeatherIcon name="maximize-2" class="w-3.5 h-3.5" />
              </button>
            </div>
          </Transition>
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

  <TemplatePicker
    v-if="showTemplatePicker"
    :submit="onTemplateSubmit"
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
      <p class="text-xs text-ink-gray-5">
        A copy with a <strong>[TEST]</strong> subject prefix will be sent to your account:
      </p>
      <p class="text-sm font-medium text-ink-gray-8 mt-1">{{ testRecipient }}</p>
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
    title="Check Links"
    size="md"
    @update:model-value="(v) => { if (!v) showLinkChecker = false }"
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
          <Tooltip v-if="linkResults.filter(r => r.status === 'blocked').length" text="Could not verify from this server (DNS or network unreachable). Links likely work fine for recipients.">
            <Badge theme="orange" variant="subtle" size="sm">
              <template #prefix><FeatherIcon name="shield-off" class="w-3 h-3" /></template>
              {{ linkResults.filter(r => r.status === 'blocked').length }} blocked
            </Badge>
          </Tooltip>
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
              'border-outline-amber-2 bg-surface-amber-1': r.status === 'blocked',
            }"
          >
            <!-- Top row: url + badge -->
            <div class="flex items-center gap-2 min-w-0">
              <FeatherIcon
                :name="r.status === 'ok' ? 'check-circle' : r.status === 'skipped' ? 'minus' : r.status === 'blocked' ? 'shield-off' : 'alert-circle'"
                class="w-3.5 h-3.5 flex-shrink-0"
                :class="r.status === 'ok' ? 'text-green-500' : r.status === 'skipped' ? 'text-ink-gray-3' : r.status === 'blocked' ? 'text-orange-500' : 'text-red-500'"
              />
              <span class="text-xs font-mono text-ink-gray-7 truncate flex-1 min-w-0">{{ r.url }}</span>
              <Tooltip v-if="r.status === 'blocked'" text="Server blocked automated requests. Link likely works for real recipients.">
                <Badge theme="orange" variant="subtle" size="sm" class="flex-shrink-0">Blocked</Badge>
              </Tooltip>
              <Badge
                v-else-if="r.status !== 'ok'"
                :theme="r.status === 'skipped' ? 'gray' : 'red'"
                variant="subtle"
                size="sm"
                class="flex-shrink-0"
              >{{ r.status === 'skipped' ? 'Non-HTTP' : r.code ? `${r.code}` : 'Unreachable' }}</Badge>
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
          format="D MMM YYYY"
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
        Sending on {{ formatScheduledAt(scheduleDate + ' ' + scheduleTime) }}
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
import { ref, computed, watch } from "vue";
import { Button, TextInput, FeatherIcon, Dialog, Dropdown, Tooltip, Progress, Badge, DatePicker, TimePicker } from "frappe-ui";
import { useDark, useToggle } from "@vueuse/core";
import { useEditorStore } from "../stores/editor";
import { injectGoogleFonts } from "../fonts";
import Inspector from "../components/Inspector.vue";
import LayersPanel from "../components/LayersPanel.vue";
import CampaignSettings from "../components/CampaignSettings.vue";
import TemplatePicker from "../components/TemplatePicker.vue";
import BlockAdderRow from "../components/BlockAdderRow.vue";
import BlockRenderer from "../components/BlockRenderer.vue";
import { useZoom } from "../composables/useZoom";
import { usePanelResize } from "../composables/usePanelResize";
import { useBlockPicker } from "../composables/useBlockPicker";
import { useCampaign } from "../composables/useCampaign";
import { usePreview } from "../composables/usePreview";
import { useLinkChecker } from "../composables/useLinkChecker";
import { useTestEmail } from "../composables/useTestEmail";
import { useKeyboardShortcuts } from "../composables/useKeyboardShortcuts";
import { formatScheduledAt, collectFontFamilies } from "../utils/builderHelpers";

const editorStore = useEditorStore();
const isDark = useDark({ attribute: "data-theme", valueDark: "dark", valueLight: "light" });
const toggleDark = useToggle(isDark);
const showShortcuts = ref(false);

// ── Campaign document lifecycle (fields, save/send/schedule/duplicate) ─────────
const {
  subject, previewText, recipientConfig,
  showSettings, showTemplatePicker, showScheduleModal,
  saving, savedFlash, loadingCampaign, duplicating, scheduling,
  scheduleDate, scheduleTime, minScheduleDate, openScheduleModal,
  sendProgress, campaignStatus,
  onTemplateSubmit, saveNow,
  sendCampaign, scheduleCampaign, duplicateCampaign,
} = useCampaign(editorStore);

const { openPreview } = usePreview(editorStore, previewText);
const { showLinkChecker, linkResults, checkingLinks, openLinkChecker, applyLinkFix } = useLinkChecker(editorStore);
const { showTestModal, testSending, testRecipient, openTestModal, sendTest } = useTestEmail(editorStore, { subject, previewText });

const isMac = navigator.platform.startsWith("Mac") || navigator.userAgent.includes("Mac");
const MOD = isMac ? "⌘" : "Ctrl";
const SHORTCUTS = [
  { label: "Undo",             keys: [MOD, "Z"] },
  { label: "Redo",             keys: [MOD, "⇧", "Z"] },
  { label: "Save",             keys: [MOD, "S"] },
  { label: "Copy block",       keys: [MOD, "C"] },
  { label: "Paste block",      keys: [MOD, "V"] },
  { label: "Duplicate block",  keys: [MOD, "D"] },
  { label: "Delete block",     keys: ["⌫"] },
  { label: "Deselect",         keys: ["Esc"] },
  { label: "Preview",          keys: [MOD, "⇧", "P"] },
  { label: "Zoom in",          keys: [MOD, "+"] },
  { label: "Zoom out",         keys: [MOD, "−"] },
  { label: "Reset zoom",       keys: [MOD, "0"] },
];

const { canvasZoom, zoomVisible, resetZoom, stepZoom } = useZoom();

useKeyboardShortcuts({ editorStore, saveNow, openPreview, stepZoom, canvasZoom });

// Left brand dropdown (Frappe Builder-style): navigation + page-level actions
// that don't belong in the always-visible toolbar.
const menuOptions = computed(() => [
  {
    group: "navigate",
    hideLabel: true,
    items: [
      {
        label: "Back to Letters",
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
        label: "Duplicate Letter",
        icon: "copy",
        onClick: duplicateCampaign,
        disabled: !editorStore.campaignDoc || duplicating.value,
      },
      {
        label: "Settings",
        icon: "settings",
        onClick: () => (showSettings.value = true),
      },
      {
        label: "Shortcuts",
        icon: "command",
        onClick: () => (showShortcuts.value = true),
      },
      {
        label: "Toggle theme",
        icon: isDark.value ? "sun" : "moon",
        onClick: () => toggleDark(),
      },
    ],
  },
]);
const previewOptions = computed(() => [
  { label: "Preview", icon: "external-link", onClick: openPreview },
  { label: "Send test email", icon: "send", onClick: openTestModal },
  { label: "Check links", icon: "link", onClick: openLinkChecker },
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
    onClick: openScheduleModal,
    disabled: !editorStore.campaignDoc,
  },
]);

// ── Panel resize ──────────────────────────────────────────────────────────────
const { leftPanelWidth, rightPanelWidth, startLeftResize, startRightResize } = usePanelResize();

// ── Block picker (sidebar add-block list + hover preview + drop) ───────────────
const {
  pickerTarget, openPicker, availableBlocks,
  onAddBlock, addContainer, closePicker, insertBlock,
  blockPreview, showBlockPreview, hideBlockPreview, onCanvasDrop,
} = useBlockPicker(editorStore);

// ── Google Fonts injection ───────────────────────────────────────────────────
// Watch the block tree for web-font usage and inject <link> tags so the editor
// preview renders the correct weights. Runs immediately on mount (immediate:true)
// and again whenever any font_family prop changes.
watch(
  () => collectFontFamilies(editorStore.blocks),
  (names) => injectGoogleFonts(names),
  { immediate: true, deep: false }
);


</script>

<style>
/* Ensure frappe-ui Dialog overlay sits above all canvas z-index layers */
.dialog-overlay {
  z-index: 9999 !important;
}
/* Tailwind's `transform` class on dialog-content creates a CSS containing block
   for position:fixed, which breaks Reka UI PopoverPortal (DatePicker calendar)
   positioning. Remove it so popovers position relative to the real viewport. */
.dialog-content {
  transform: none !important;
}

/* Save flash fade transition */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* Placeholder text for contenteditable fields */
.editable-placeholder:empty::before {
  content: attr(data-placeholder);
  color: #d1d5db;
  pointer-events: none;
}
</style>
