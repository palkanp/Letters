<template>
  <div class="letter-builder flex flex-col bg-surface-gray-1 font-sans overflow-hidden" style="height: 100vh">

    <!-- ── Top bar ─────────────────────────────────────────────────────────── -->
    <BuilderToolbar
      :menu-options="menuOptions"
      :preview-options="previewOptions"
      :send-options="sendOptions"
      :letter-status="letterStatus"
      :send-progress="sendProgress"
      :saving="saving"
      :saved-flash="savedFlash"
      :letter-name="editorStore.letterName"
      :scheduled-at="editorStore.letterDoc?.scheduled_at || ''"
      :can-send="!!editorStore.letterDoc && !editorStore.letterDoc.has_notification"
      @add-block="onAddBlock"
      @add-container="addContainer"
      @insert="insertBlock"
      @open-settings="showSettings = true"
    />

    <!-- ── Body ──────────────────────────────────────────────────────────────── -->
    <div class="flex flex-1 overflow-hidden">

      <!-- Left sidebar: Layers panel (block picker replaces it when open) -->
      <aside
        class="flex-shrink-0 bg-surface-base border-r border-outline-gray-1 flex flex-col relative"
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
            <Button variant="ghost" size="sm" icon="lucide-x" aria-label="Close picker" @click="closePicker" />
          </template>
          <template v-else>
            <span class="text-xs font-semibold text-ink-gray-4 uppercase tracking-widest">Layers</span>
            <span class="text-xs text-ink-gray-3 tabular-nums">{{ editorStore.blocks.length }}</span>
          </template>
        </div>

        <!-- Block picker list (shown when pickerTarget is set) -->
        <div v-if="pickerTarget !== null" class="flex-1 overflow-y-auto min-h-0 py-1">
          <template v-for="b in availableBlocks" :key="b.section || b.type">
            <div
              v-if="b.section"
              class="px-4 pt-3 pb-1 text-xs font-semibold text-ink-gray-4 uppercase tracking-widest select-none"
            >{{ b.section }}</div>
            <Button
              v-else
              variant="ghost"
              class="w-full px-4 py-1.5 text-ink-gray-7 !justify-start"
              :iconLeft="`lucide-${b.icon}`"
              @mouseenter="(e) => showBlockPreview(b.type, e)"
              @mouseleave="hideBlockPreview"
              @click="insertBlock(b.type)"
            >
              {{ b.label }}
            </Button>
          </template>
        </div>

        <!-- Layers panel -->
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
            <div style="overflow:hidden;height:240px;position:relative;background:#1a1a1a;">
              <div class="letters-email-canvas" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) scale(0.6);transform-origin:center center;width:600px;background:#ffffff;">
                <BlockRenderer :block="blockPreview.block" :index="0" />
              </div>
            </div>
          </div>
        </div>
      </Teleport>

      <!-- Canvas -->
      <main
        class="flex-1 overflow-y-auto p-6 relative bg-surface-gray-2"
        @dragover.prevent
        @drop="onCanvasDrop"
        @click="editorStore.selectBlock(null)"
      >
        <div
          class="mx-auto origin-top transition-transform shadow-sm letters-email-canvas"
          :style="{ backgroundColor: editorStore.canvasBg || '#ffffff', maxWidth: editorStore.emailWidth + 'px', minHeight: '200px', transform: `scale(${canvasZoom})`, transformOrigin: 'top center', marginBottom: canvasZoom < 1 ? `calc((${canvasZoom} - 1) * 100%)` : undefined, color: '#374151', colorScheme: 'light' }"
        >

          <!-- Loading skeleton (while fetching a saved letter) -->
          <div v-if="loadingLetter" class="p-6 space-y-3" aria-busy="true" aria-label="Loading letter">
            <div v-for="n in 4" :key="n" class="h-16 bg-surface-gray-2 animate-pulse rounded-lg" />
          </div>

          <!-- Empty state (not loading, no blocks) -->
          <div
            v-else-if="!editorStore.blocks.length"
            class="border-2 border-dashed border-outline-gray-2 rounded-xl p-16 text-center select-none"
          >
            <div class="mb-3 opacity-40"><span class="lucide-inbox size-10 mx-auto text-ink-gray-4 block" aria-hidden="true" /></div>
            <p class="text-sm font-medium mb-1">Your canvas is empty</p>
            <p class="text-xs opacity-60">Click <strong>+</strong> in the toolbar to add your first block</p>
          </div>

          <!-- Block list with inline adders -->
          <template v-else-if="!loadingLetter">
            <!-- Read-only notice for sent/sending letters -->
            <div
              v-if="editorStore.isReadOnly"
              class="flex items-center gap-2 px-4 py-2.5 bg-surface-gray-2 border-b border-outline-gray-1 text-xs text-ink-gray-5 select-none"
            >
              <span class="lucide-lock size-3.5 flex-shrink-0" aria-hidden="true" />
              This letter has been sent and is read-only.
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

        <!-- Zoom indicator — sticky to the viewport bottom -->
        <div class="sticky bottom-0 z-20 flex justify-center pointer-events-none pb-4 pt-4">
          <Transition name="fade">
            <div
              v-show="zoomVisible"
              class="pointer-events-auto flex items-center gap-2 bg-ink-gray-9 text-ink-white rounded-full shadow-lg pl-3.5 pr-1.5 py-1"
              @mouseenter="zoomVisible = true"
            >
              <span class="text-xs font-medium tabular-nums select-none">{{ Math.round(canvasZoom * 100) }}%</span>
              <Button
                variant="ghost"
                icon="lucide-maximize-2"
                size="sm"
                class="!w-6 !h-6 !rounded-full !text-ink-white hover:!bg-ink-white/15"
                title="Reset to 100%"
                @click.stop="resetZoom"
              />
            </div>
          </Transition>
        </div>
      </main>

      <!-- Drag handle + Inspector (hidden for read-only letters) -->
      <template v-if="!editorStore.isReadOnly">
        <div
          class="flex-shrink-0 w-1 bg-transparent hover:bg-blue-400 cursor-col-resize z-[1] transition-colors"
          @mousedown="startRightResize"
        />
        <Inspector :width="rightPanelWidth" />
      </template>

    </div>
  </div>

  <LetterSettings
    v-model="showSettings"
    :letter-name="editorStore.letterName"
    @update:letter-name="(v) => (editorStore.letterName = v)"
    v-model:subject="subject"
    v-model:preview-text="previewText"
    v-model:recipient-config="recipientConfig"
    v-model:include-unsubscribe="includeUnsubscribe"
    :letter-doc="editorStore.letterDoc"
    :initial-tab="settingsInitialTab"
  />

  <TemplatePicker
    v-if="showTemplatePicker"
    :submit="onTemplateSubmit"
    @close="onTemplateClose"
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
    @schedule="scheduleLetter"
  />

</template>

<script setup>
import { ref, computed, watch } from "vue";
import { Button } from "frappe-ui";
import { useEditorStore } from "../stores/editor";
import { injectGoogleFonts } from "../fonts";
import Inspector from "../components/Inspector.vue";
import LayersPanel from "../components/LayersPanel.vue";
import LetterSettings from "../components/LetterSettings.vue";
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
import { useLetter } from "../composables/useLetter";
import { usePreview } from "../composables/usePreview";
import { useLinkChecker } from "../composables/useLinkChecker";
import { useTestEmail } from "../composables/useTestEmail";
import { useKeyboardShortcuts } from "../composables/useKeyboardShortcuts";
import { formatScheduledAt, collectFontFamilies } from "../utils/builderHelpers";

const props = defineProps({
  initialName: { type: String, default: null },
  isDark: { type: Boolean, default: false },
  toggleDark: { type: Function, default: () => {} },
});
const emit = defineEmits(["close"]);

const editorStore = useEditorStore();
const showShortcuts = ref(false);

const {
  subject, previewText, recipientConfig, includeUnsubscribe,
  showSettings, showTemplatePicker, showScheduleModal, settingsInitialTab,
  saving, savedFlash, loadingLetter, duplicating, scheduling,
  scheduleDate, scheduleTime, minScheduleDate, openScheduleModal,
  sendProgress, letterStatus,
  onTemplateSubmit, onTemplateClose, saveNow, saveLetter,
  sendLetter, scheduleLetter, duplicateLetter,
} = useLetter(editorStore, { initialName: props.initialName, onClose: () => emit("close") });

const { openPreview } = usePreview(editorStore, previewText);
const { showLinkChecker, linkResults, checkingLinks, openLinkChecker, applyLinkFix } = useLinkChecker(editorStore, { flushSave: saveLetter });
const { showTestModal, testSending, testRecipient, openTestModal, sendTest } = useTestEmail(editorStore, { subject, previewText, flushSave: saveLetter });

watch(showSettings, (open) => { if (!open && editorStore.isDirty) saveNow(); });

const { canvasZoom, zoomVisible, resetZoom, stepZoom } = useZoom();

useKeyboardShortcuts({ editorStore, saveNow, openPreview, stepZoom, canvasZoom });

const menuOptions = computed(() => [
  {
    group: "navigate",
    hideLabel: true,
    items: [
      {
        label: "Back to Letters",
        icon: "lucide-arrow-left",
        onClick: () => emit("close"),
      },
    ],
  },
  {
    group: "letter",
    hideLabel: true,
    items: [
      {
        label: "Duplicate Letter",
        icon: "lucide-copy",
        onClick: duplicateLetter,
        disabled: !editorStore.letterDoc || duplicating.value,
      },
      {
        label: "Settings",
        icon: "lucide-settings",
        onClick: () => (showSettings.value = true),
      },
      {
        label: "Shortcuts",
        icon: "lucide-command",
        onClick: () => (showShortcuts.value = true),
      },
      {
        label: "Toggle theme",
        icon: props.isDark ? "lucide-sun" : "lucide-moon",
        onClick: () => props.toggleDark(),
      },
    ],
  },
]);
const previewOptions = computed(() => [
  { label: "Preview", icon: "lucide-external-link", onClick: openPreview },
  { label: "Send test email", icon: "lucide-send", onClick: openTestModal },
  { label: "Check links", icon: "lucide-link", onClick: openLinkChecker },
]);

const sendOptions = computed(() => [
  {
    label: "Send now",
    icon: "lucide-send",
    onClick: sendLetter,
    disabled: !editorStore.letterDoc,
  },
  {
    label: "Schedule sending",
    icon: "lucide-clock",
    onClick: openScheduleModal,
    disabled: !editorStore.letterDoc,
  },
]);

const { leftPanelWidth, rightPanelWidth, startLeftResize, startRightResize } = usePanelResize();

const {
  pickerTarget, openPicker, availableBlocks,
  onAddBlock, addContainer, closePicker, insertBlock,
  blockPreview, showBlockPreview, hideBlockPreview, onCanvasDrop,
} = useBlockPicker(editorStore);

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
