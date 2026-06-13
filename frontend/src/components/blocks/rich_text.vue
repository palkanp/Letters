<template>
  <BlockWrapper :block="block" :index="index">
    <div :style="paddingStyle">
      <!-- frappe-ui TextEditor (TipTap). A bubble menu provides bold/italic/
           underline/link/lists on selection, replacing the old execCommand
           toolbar and contenteditable. Block-level font + alignment styling is
           applied via the wrapper + editorClass. -->
      <div
        class="rich-text-shell"
        :style="{
          fontFamily:    fontStack(block.props.font_family, 'Arial, Helvetica, sans-serif'),
          fontSize:      block.props.font_size      || '15px',
          fontWeight:    block.props.font_weight    || '400',
          color:         block.props.text_color     || '#374151',
          lineHeight:    block.props.line_height    || '1.6',
          textAlign:     block.props.align          || 'left',
          letterSpacing: block.props.letter_spacing || 'normal',
        }"
        @click.stop="store.selectBlock(block.id)"
      >
        <!-- Static placeholder when empty and not selected (TipTap doesn't show placeholder when not editable) -->
        <div
          v-if="!isSelected && !block.props.html_content"
          class="rich-text-content min-h-10 text-ink-gray-3 select-none pointer-events-none"
        >Text</div>
        <TextEditor
          v-else
          :content="block.props.html_content || ''"
          :editable="isSelected"
          placeholder="Text"
          :bubble-menu="bubbleMenuButtons"
          editor-class="rich-text-content outline-none min-h-10"
          @change="onChange"
        />
      </div>
    </div>
  </BlockWrapper>
</template>

<script setup>
import { computed } from "vue";
import { TextEditor } from "frappe-ui";
import BlockWrapper from "../BlockWrapper.vue";
import { useEditorStore } from "../../stores/editor";
import { usePadding } from "../../composables/usePadding";
import { fontStack } from "../../fonts";

const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();

const blockProps   = computed(() => props.block.props);
const paddingStyle = usePadding(blockProps, { top: 20, right: 16, bottom: 20, left: 16 });

const isSelected = computed(() => store.selectedBlockId === props.block.id);

// Formatting options in the bubble menu.
// Bold is omitted — font weight is controlled block-level via the inspector's
// Weight field; keeping Bold here would visually conflict with that setting.
const bubbleMenuButtons = [
  "Italic",
  "Underline",
  "Strikethrough",
  "Link",
  "Bullet List",
  "Numbered List",
];

function onChange(html) {
  // Only persist real changes to avoid churning history on focus.
  if (html !== (props.block.props.html_content || "")) {
    store.updateBlockProps(props.block.id, { html_content: html });
  }
}

</script>

<style>
/* Show placeholder even when the block is not selected (not focused).
   TipTap normally gates the placeholder behind :focus — we override that. */
/* Bubble menu: give it an elevated surface so it doesn't blend into the canvas */
.bubble-menu {
  background-color: var(--surface-white, #ffffff) !important;
  border: 1px solid var(--outline-gray-2, #e5e7eb) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
  border-radius: 6px !important;
}

.rich-text-shell .ProseMirror p.is-editor-empty:first-child::before {
  color: #d1d5db;
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}

/* Force TipTap's ProseMirror to inherit block-level styles from the shell wrapper.
   frappe-ui's TextEditor CSS may reset font-size/color/line-height on .ProseMirror. */
.rich-text-shell .ProseMirror {
  font-size: inherit !important;
  font-weight: inherit !important;
  color: inherit !important;
  line-height: inherit !important;
  font-family: inherit !important;
}
/* Inline + block elements: inherit all block-level styles */
.rich-text-shell .ProseMirror p,
.rich-text-shell .ProseMirror li,
.rich-text-shell .ProseMirror span,
.rich-text-shell .ProseMirror strong,
.rich-text-shell .ProseMirror b,
.rich-text-shell .ProseMirror em,
.rich-text-shell .ProseMirror i {
  font-size: inherit !important;
  font-weight: inherit !important;
  color: inherit !important;
  line-height: inherit !important;
  font-family: inherit !important;
  text-align: inherit !important;
  letter-spacing: inherit !important;
}

/* Headings: same overrides + reset browser default heading margin */
.rich-text-shell .ProseMirror h1,
.rich-text-shell .ProseMirror h2,
.rich-text-shell .ProseMirror h3,
.rich-text-shell .ProseMirror h4,
.rich-text-shell .ProseMirror h5,
.rich-text-shell .ProseMirror h6 {
  font-size: inherit !important;
  font-weight: inherit !important;
  color: inherit !important;
  line-height: inherit !important;
  font-family: inherit !important;
  text-align: inherit !important;
  letter-spacing: inherit !important;
  margin: 0 !important;
}

.rich-text-content ul {
  list-style-type: disc;
  list-style-position: inside;
  padding-left: 0;
  margin: 0.5em 0;
}
.rich-text-content ol {
  list-style-type: decimal;
  list-style-position: inside;
  padding-left: 0;
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
