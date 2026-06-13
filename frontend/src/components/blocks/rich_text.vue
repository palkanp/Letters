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

const bubbleMenuButtons = [
  "Bold",
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
/* Bubble menu: TipTap uses @floating-ui/dom (no Tippy wrapper), so the
   .bubble-menu div renders directly. Force a white surface so it's always
   readable over the light canvas regardless of the page dark/light mode. */
.bubble-menu,
.bubble-menu .inline-flex {
  background-color: #ffffff !important;
}
.bubble-menu {
  border: 1px solid #e5e7eb !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.14) !important;
  border-radius: 8px !important;
  overflow: hidden !important;
}
.bubble-menu button,
.bubble-menu svg {
  color: #1f2937 !important;
}

.rich-text-shell .ProseMirror p.is-editor-empty:first-child::before {
  color: #d1d5db;
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}

/* Tailwind Typography's .prose class (added by frappe-ui's TextEditor) applies
   max-width: 65ch (~540px). Override it so the editor fills the full block width. */
.rich-text-shell .prose {
  max-width: none !important;
}

/* Force ProseMirror root to inherit the shell's block-level styles.
   Only the root needs !important — child elements inherit naturally from it.
   Using !important only here avoids overriding TipTap's inline style spans. */
.rich-text-shell .ProseMirror {
  font-size: inherit !important;
  font-weight: inherit !important;
  color: inherit !important;
  line-height: inherit !important;
  font-family: inherit !important;
  letter-spacing: inherit !important;
}

/* Child elements: use !important so block-level props always win over any inline
   styles that may have been pasted in from external sources (Word, Google Docs, etc.).
   This matches what the email preview does — _sanitize_rich_html strips all inline
   styles, so only the block props control the appearance in both views.
   strong/b are excluded from font-weight so Bold markup renders at 700. */
.rich-text-shell .ProseMirror p,
.rich-text-shell .ProseMirror li,
.rich-text-shell .ProseMirror span,
.rich-text-shell .ProseMirror em,
.rich-text-shell .ProseMirror i,
.rich-text-shell .ProseMirror strong,
.rich-text-shell .ProseMirror b {
  font-size: inherit !important;
  color: inherit !important;
  line-height: inherit !important;
  font-family: inherit !important;
  letter-spacing: inherit !important;
  text-align: inherit !important;
}

/* Headings: reset browser margins + inherit block styles */
.rich-text-shell .ProseMirror h1,
.rich-text-shell .ProseMirror h2,
.rich-text-shell .ProseMirror h3,
.rich-text-shell .ProseMirror h4,
.rich-text-shell .ProseMirror h5,
.rich-text-shell .ProseMirror h6 {
  font-size: inherit;
  font-weight: inherit;
  color: inherit;
  line-height: inherit;
  font-family: inherit;
  letter-spacing: inherit;
  text-align: inherit !important;
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
/* Marker (bullet/number) matches the block-level font/weight/color */
.rich-text-shell .ProseMirror li::marker {
  font-size: inherit;
  font-weight: inherit;
  color: inherit;
  font-family: inherit;
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
