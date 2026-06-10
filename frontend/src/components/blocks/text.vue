<template>
  <BlockWrapper :block="block" :index="index">
    <div :style="paddingStyle">
      <div
        ref="contentRef"
        class="outline-none min-h-10 leading-relaxed"
        :class="alignClass"
        :style="{
          fontSize: block.props.font_size,
          fontWeight: block.props.font_weight,
          color: block.props.text_color,
          lineHeight: block.props.line_height || '1.6',
          letterSpacing: block.props.letter_spacing || 'normal',
        }"
        contenteditable="true"
        @focus="onFocus"
        @blur="onBlur"
        @paste.prevent="onPaste"
        @keydown="onKeydown"
        @click.stop="store.selectBlock(block.id)"
      />
    </div>
  </BlockWrapper>
</template>

<script setup>
import { computed } from "vue";
import BlockWrapper from "../BlockWrapper.vue";
import { useEditorStore } from "../../stores/editor";
import { usePadding } from "../../composables/usePadding";
import { useContentEditable } from "../../composables/useContentEditable";

const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();
function update(key, val) { store.updateBlockProps(props.block.id, { [key]: val }); }

const blockProps = computed(() => props.block.props);
const paddingStyle = usePadding(blockProps);

const { elRef: contentRef, onFocus, onBlur, onPaste, onKeydown } = useContentEditable(
  () => props.block.props.content,
  (val) => update("content", val),
  { multiline: true },
);

const alignClass = computed(() => ({
  "text-left":   props.block.props.align === "left" || !props.block.props.align,
  "text-center": props.block.props.align === "center",
  "text-right":  props.block.props.align === "right",
}));
</script>
