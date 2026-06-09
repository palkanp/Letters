<template>
  <BlockWrapper :block="block" :index="index">
    <div :style="paddingStyle">

      <!-- ── Formatting toolbar (only when this block is selected) ──────────── -->
      <div
        v-if="isSelected"
        class="flex items-center gap-0.5 mb-2 px-1 py-1 bg-gray-50 border border-gray-200 rounded-lg select-none"
      >
        <!-- Bold -->
        <button
          type="button"
          title="Bold (Cmd+B)"
          class="w-7 h-7 flex items-center justify-center rounded text-gray-700 font-bold text-sm hover:bg-white hover:shadow-sm transition-colors"
          @mousedown.prevent="exec('bold')"
        >B</button>

        <!-- Italic -->
        <button
          type="button"
          title="Italic (Cmd+I)"
          class="w-7 h-7 flex items-center justify-center rounded text-gray-600 italic text-sm hover:bg-white hover:shadow-sm transition-colors"
          @mousedown.prevent="exec('italic')"
        >I</button>

        <!-- Underline -->
        <button
          type="button"
          title="Underline (Cmd+U)"
          class="w-7 h-7 flex items-center justify-center rounded text-gray-600 underline text-sm hover:bg-white hover:shadow-sm transition-colors"
          @mousedown.prevent="exec('underline')"
        >U</button>

        <div class="w-px h-4 bg-gray-200 mx-0.5 flex-shrink-0" />

        <!-- Bullet list -->
        <button
          type="button"
          title="Bullet list"
          class="w-7 h-7 flex items-center justify-center rounded text-gray-600 hover:bg-white hover:shadow-sm transition-colors"
          @mousedown.prevent="exec('insertUnorderedList')"
        >
          <FeatherIcon name="list" class="w-3.5 h-3.5" />
        </button>

        <!-- Numbered list -->
        <button
          type="button"
          title="Numbered list"
          class="w-7 h-7 flex items-center justify-center rounded text-gray-600 hover:bg-white hover:shadow-sm transition-colors text-xs font-mono"
          @mousedown.prevent="exec('insertOrderedList')"
        >1.</button>

        <div class="w-px h-4 bg-gray-200 mx-0.5 flex-shrink-0" />

        <!-- Link -->
        <button
          type="button"
          title="Insert link"
          class="w-7 h-7 flex items-center justify-center rounded text-gray-600 hover:bg-white hover:shadow-sm transition-colors"
          :class="{ 'bg-blue-50 text-blue-600': showLinkInput }"
          @mousedown.prevent="toggleLinkInput"
        >
          <FeatherIcon name="link" class="w-3.5 h-3.5" />
        </button>

        <!-- Remove link -->
        <button
          type="button"
          title="Remove link"
          class="w-7 h-7 flex items-center justify-center rounded text-gray-600 hover:bg-white hover:shadow-sm transition-colors"
          @mousedown.prevent="exec('unlink')"
        >
          <FeatherIcon name="link-2" class="w-3.5 h-3.5" />
        </button>

        <div class="w-px h-4 bg-gray-200 mx-0.5 flex-shrink-0" />

        <!-- Clear formatting -->
        <button
          type="button"
          title="Clear formatting"
          class="w-7 h-7 flex items-center justify-center rounded text-gray-600 hover:bg-white hover:shadow-sm transition-colors"
          @mousedown.prevent="exec('removeFormat')"
        >
          <FeatherIcon name="type" class="w-3.5 h-3.5" />
        </button>
      </div>

      <!-- ── Link URL input row ─────────────────────────────────────────────── -->
      <div v-if="isSelected && showLinkInput" class="flex items-center gap-1 mb-2">
        <input
          ref="linkInputRef"
          v-model="linkUrl"
          type="text"
          placeholder="https://example.com"
          class="flex-1 text-xs border border-gray-200 rounded-md px-2 py-1.5 outline-none focus:border-blue-400 bg-white"
          @keydown.enter.prevent="applyLink"
          @keydown.escape.prevent="closeLinkInput"
        />
        <button
          type="button"
          class="text-xs px-2.5 py-1.5 bg-gray-900 text-white rounded-md hover:bg-gray-700 transition-colors"
          @click="applyLink"
        >Apply</button>
        <button
          type="button"
          class="text-xs px-2.5 py-1.5 bg-gray-100 text-gray-600 rounded-md hover:bg-gray-200 transition-colors"
          @click="closeLinkInput"
        >Cancel</button>
      </div>

      <!-- ── The actual editable area ──────────────────────────────────────── -->
      <div
        ref="editorRef"
        contenteditable="true"
        class="outline-none min-h-10 rich-text-content"
        :class="alignClass"
        :style="{
          fontSize:      block.props.font_size   || '15px',
          fontWeight:    block.props.font_weight || '400',
          color:         block.props.text_color  || '#374151',
          lineHeight:    block.props.line_height || '1.6',
        }"
        @focus="onFocus"
        @blur="onBlur"
        @paste="onPaste"
        @click.stop="store.selectBlock(block.id)"
      />
    </div>
  </BlockWrapper>
</template>

<script setup>
import { ref, computed, watchEffect, nextTick } from "vue";
import { FeatherIcon } from "frappe-ui";
import BlockWrapper from "../BlockWrapper.vue";
import { useEditorStore } from "../../stores/editor";
import { usePadding } from "../../composables/usePadding";

const props  = defineProps({ block: Object, index: Number });
const store  = useEditorStore();
function update(key, val) { store.updateBlockProps(props.block.id, { [key]: val }); }

const blockProps   = computed(() => props.block.props);
const paddingStyle = usePadding(blockProps, { top: 20, right: 32, bottom: 20, left: 32 });

const isSelected = computed(() => store.selectedBlockId === props.block.id);

const editorRef    = ref(null);
const linkInputRef = ref(null);
const _focused     = ref(false);
const showLinkInput = ref(false);
const linkUrl       = ref("");

// Saved selection range — preserved across toolbar interactions
let _savedRange = null;

// ── Sync store → DOM (only when not focused) ──────────────────────────────
watchEffect(() => {
  const el  = editorRef.value;
  const val = props.block.props.html_content ?? "";
  if (!_focused.value && el) {
    // innerHTML, not textContent — this is the rich text block
    el.innerHTML = val;
  }
});

function onFocus() {
  _focused.value = true;
}

function onBlur() {
  _focused.value = false;
  if (editorRef.value) {
    update("html_content", editorRef.value.innerHTML);
  }
}

// ── Paste: allow basic rich-text tags, strip the rest ────────────────────
function onPaste(e) {
  e.preventDefault();
  // Try HTML first; fall back to plain text
  const html = e.clipboardData.getData("text/html");
  const text = e.clipboardData.getData("text/plain");

  if (html) {
    // Strip everything except allowed inline tags via a temporary DOM parse
    const tmp = document.createElement("div");
    tmp.innerHTML = html;
    // Remove script/style/meta nodes
    tmp.querySelectorAll("script,style,meta,link,head").forEach(n => n.remove());
    // Walk and keep only text + allowed tags
    const allowed = new Set(["A","B","STRONG","I","EM","U","UL","OL","LI","BR","P","SPAN"]);
    function flatten(node) {
      if (node.nodeType === Node.TEXT_NODE) return;
      for (const child of [...node.childNodes]) {
        flatten(child);
      }
      if (node.nodeType === Node.ELEMENT_NODE && !allowed.has(node.tagName)) {
        // Replace disallowed element with its children
        node.replaceWith(...node.childNodes);
      }
    }
    flatten(tmp);
    document.execCommand("insertHTML", false, tmp.innerHTML);
  } else {
    document.execCommand("insertText", false, text);
  }
}

// ── Toolbar commands ──────────────────────────────────────────────────────
function exec(command, value = null) {
  // Restore focus to editor before running command
  if (editorRef.value && document.activeElement !== editorRef.value) {
    editorRef.value.focus();
  }
  document.execCommand(command, false, value);
}

// ── Link handling ─────────────────────────────────────────────────────────
function saveSelection() {
  const sel = window.getSelection();
  if (sel && sel.rangeCount > 0) {
    _savedRange = sel.getRangeAt(0).cloneRange();
  }
}

function restoreSelection() {
  if (_savedRange) {
    editorRef.value?.focus();
    const sel = window.getSelection();
    if (sel) {
      sel.removeAllRanges();
      sel.addRange(_savedRange);
    }
  }
}

function toggleLinkInput() {
  if (showLinkInput.value) {
    closeLinkInput();
    return;
  }
  saveSelection();
  showLinkInput.value = true;
  linkUrl.value = "";
  nextTick(() => linkInputRef.value?.focus());
}

function applyLink() {
  const url = linkUrl.value.trim();
  if (url) {
    restoreSelection();
    document.execCommand("createLink", false, url);
    // Make links open in new tab in the canvas preview
    nextTick(() => {
      editorRef.value?.querySelectorAll("a").forEach(a => {
        a.target = "_blank";
        a.rel = "noopener";
      });
      update("html_content", editorRef.value?.innerHTML || "");
    });
  }
  closeLinkInput();
}

function closeLinkInput() {
  showLinkInput.value = false;
  linkUrl.value = "";
  _savedRange = null;
}

// ── Alignment ─────────────────────────────────────────────────────────────
const alignClass = computed(() => ({
  "text-left":   props.block.props.align === "left"   || !props.block.props.align,
  "text-center": props.block.props.align === "center",
  "text-right":  props.block.props.align === "right",
}));
</script>

<style>
/* Scoped-ish: target the editor's inline rich content */
.rich-text-content ul {
  list-style-type: disc;
  padding-left: 1.5em;
  margin: 0.5em 0;
}
.rich-text-content ol {
  list-style-type: decimal;
  padding-left: 1.5em;
  margin: 0.5em 0;
}
.rich-text-content li {
  margin: 0.2em 0;
}
.rich-text-content a {
  color: #2563eb;
  text-decoration: underline;
}
.rich-text-content p {
  margin: 0 0 0.5em;
}
.rich-text-content p:last-child {
  margin-bottom: 0;
}
</style>
