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
          fontFamily: fontStack(block.props.font_family, 'Arial, Helvetica, sans-serif'),
          fontSize:   block.props.font_size   || '15px',
          fontWeight: block.props.font_weight || '400',
          color:      block.props.text_color  || '#374151',
          lineHeight: block.props.line_height || '1.6',
          textAlign:  block.props.align       || 'left',
        }"
        @click.stop="store.selectBlock(block.id)"
      >
        <TextEditor
          :content="block.props.html_content || ''"
          :editable="isSelected"
          placeholder="Text…"
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

// Buttons shown in the bubble menu (on text selection).
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
/* Force TipTap's ProseMirror to inherit block-level styles from the shell wrapper.
   frappe-ui's TextEditor CSS may reset font-size/color/line-height on .ProseMirror. */
.rich-text-shell .ProseMirror {
  font-size: inherit !important;
  font-weight: inherit !important;
  color: inherit !important;
  line-height: inherit !important;
  font-family: inherit !important;
}
.rich-text-shell .ProseMirror p,
.rich-text-shell .ProseMirror li,
.rich-text-shell .ProseMirror span {
  font-size: inherit;
  font-weight: inherit;
  color: inherit;
  line-height: inherit;
  font-family: inherit;
  text-align: inherit !important;
}

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
