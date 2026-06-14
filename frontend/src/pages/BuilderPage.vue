<template>
  <div class="letters-builder flex flex-col bg-surface-gray-1 font-sans overflow-hidden" style="height: 100vh">

    <!-- ── Top bar ─────────────────────────────────────────────────────────── -->
    <BuilderToolbar
      :menu-options="menuOptions"
      :preview-options="previewOptions"
      :send-options="sendOptions"
      :campaign-status="campaignStatus"
      :send-progress="sendProgress"
      :saving="saving"
      :saved-flash="savedFlash"
      :campaign-name="editorStore.campaignName"
      :scheduled-at="editorStore.campaignDoc?.scheduled_at || ''"
      :can-send="!!editorStore.campaignDoc"
      @add-block="onAddBlock"
      @add-container="addContainer"
      @insert="insertBlock"
      @open-settings="showSettings = true"
    />

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
        class="flex-1 overflow-y-auto p-6 relative"
        :style="{ backgroundColor: editorStore.canvasBg || '#f3f4f6' }"
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
            <!-- Read-only notice for sent/sending campaigns -->
            <div
              v-if="editorStore.isReadOnly"
              class="flex items-center gap-2 px-4 py-2.5 bg-surface-gray-2 border-b border-outline-gray-1 text-xs text-ink-gray-5 select-none"
            >
              <FeatherIcon name="lock" class="w-3.5 h-3.5 flex-shrink-0" />
              This campaign has been sent and is read-only.
            </div>

            <!-- Adder before first block (hidden when read-only) -->
            <BlockAdderRow v-if="!editorStore.isReadOnly" :after-index="-1" @open="(i) => openPicker({ mode: 'top', afterIndex: i })" />

            <template v-for="(block, index) in editorStore.blocks" :key="block.id">
              <BlockRenderer :block="block" :index="index" />
              <!-- Adder after each block (hidden when read-only) -->
              <BlockAdderRow v-if="!editorStore.isReadOnly" :after-index="index" @open="(i) => openPicker({ mode: 'top', afterIndex: i })" />
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

      <!-- Drag handle + Inspector (hidden for read-only campaigns) -->
      <template v-if="!editorStore.isReadOnly">
        <div
          class="flex-shrink-0 w-1 bg-transparent hover:bg-blue-400 cursor-col-resize z-[1] transition-colors"
          @mousedown="startRightResize"
        />
        <Inspector :width="rightPanelWidth" />
      </template>

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

  <ShortcutsDialog v-model="showShortcuts" />

  <TestEmailDialog
    v-model="showTestModal"
    :recipient="testRecipient"
    :sending="testSending"
    @send="sendTest"
  />

  <LinkCheckerDialog
    v-model="showLinkChecker"
    :checking="checkingLinks"
    :results="linkResults"
    @recheck="openLinkChecker"
    @fix="applyLinkFix"
  />

  <ScheduleDialog
    v-model="showScheduleModal"
    v-model:date="scheduleDate"
    v-model:time="scheduleTime"
    :min-date="minScheduleDate"
    :scheduling="scheduling"
    @schedule="scheduleCampaign"
  />

</template>

<script setup>
import { ref, computed, watch } from "vue";
import { FeatherIcon } from "frappe-ui";
import { useDark, useToggle } from "@vueuse/core";
import { useEditorStore } from "../stores/editor";
import { injectGoogleFonts } from "../fonts";
import Inspector from "../components/Inspector.vue";
import LayersPanel from "../components/LayersPanel.vue";
import CampaignSettings from "../components/CampaignSettings.vue";
import TemplatePicker from "../components/TemplatePicker.vue";
import BlockAdderRow from "../components/BlockAdderRow.vue";
import BlockRenderer from "../components/BlockRenderer.vue";
import BuilderToolbar from "../components/BuilderToolbar.vue";
import ShortcutsDialog from "../components/dialogs/ShortcutsDialog.vue";
import TestEmailDialog from "../components/dialogs/TestEmailDialog.vue";
import LinkCheckerDialog from "../components/dialogs/LinkCheckerDialog.vue";
import ScheduleDialog from "../components/dialogs/ScheduleDialog.vue";
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
  onTemplateSubmit, saveNow, saveCampaign,
  sendCampaign, scheduleCampaign, duplicateCampaign,
} = useCampaign(editorStore);

const { openPreview } = usePreview(editorStore, previewText);
const { showLinkChecker, linkResults, checkingLinks, openLinkChecker, applyLinkFix } = useLinkChecker(editorStore, { flushSave: saveCampaign });
const { showTestModal, testSending, testRecipient, openTestModal, sendTest } = useTestEmail(editorStore, { subject, previewText, flushSave: saveCampaign });

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
