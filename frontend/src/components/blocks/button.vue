<template>
  <BlockWrapper :block="block" :index="index">
    <div :style="paddingStyle">
      <div :class="alignClass">
        <span
          ref="labelRef"
          class="inline-block font-semibold cursor-text outline-none"
          :style="buttonStyle"
          contenteditable="true"
          @focus="onFocus"
          @blur="onBlur"
          @paste.prevent="onPaste"
          @keydown="onKeydown"
          @click.stop="store.selectBlock(block.id)"
        />
      </div>
    </div>
  </BlockWrapper>
</template>

<script setup>
import BlockWrapper from "../BlockWrapper.vue";
import { computed } from "vue";
import { useEditorStore } from "../../stores/editor";
import { usePadding } from "../../composables/usePadding";
import { useContentEditable } from "../../composables/useContentEditable";
import { fontStack } from "../../fonts";

const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();
function update(key, val) { store.updateBlockProps(props.block.id, { [key]: val }); }

const blockProps = computed(() => props.block.props);
const paddingStyle = usePadding(blockProps);

const { elRef: labelRef, onFocus, onBlur, onPaste, onKeydown } = useContentEditable(
  () => props.block.props.label,
  (val) => update("label", val)
);

const PADDING_MAP = {
  compact: "6px 14px",
  normal:  "10px 24px",
  large:   "14px 36px",
};

const buttonStyle = computed(() => ({
  backgroundColor: props.block.props.color,
  color:           props.block.props.text_color,
  borderRadius:    props.block.props.border_radius || "8px",
  fontFamily:      fontStack(props.block.props.font_family, "Arial, Helvetica, sans-serif"),
  fontSize:        props.block.props.font_size || "14px",
  letterSpacing:   props.block.props.letter_spacing || undefined,
  padding:         PADDING_MAP[props.block.props.button_padding] || PADDING_MAP.normal,
}));

const alignClass = computed(() => ({
  "text-left":   props.block.props.align === "left",
  "text-center": props.block.props.align === "center",
  "text-right":  props.block.props.align === "right",
}));
</script>
