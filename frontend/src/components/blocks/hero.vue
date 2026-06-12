<template>
  <BlockWrapper :block="block" :index="index">
    <div
      :style="{
        backgroundColor: block.props.background_color,
        ...paddingStyle,
      }"
      :class="textAlignClass"
    >
      <div
        ref="headingRef"
        class="font-bold outline-none mb-2 leading-tight editable-placeholder"
        data-placeholder="Heading…"
        :style="{ color: block.props.heading_color, fontSize: block.props.heading_size || '30px', fontFamily: fontStack(block.props.font_family, 'Georgia, \'Times New Roman\', serif') }"
        contenteditable="true"
        @focus="onHeadingFocus"
        @blur="onHeadingBlur"
        @paste.prevent="onHeadingPaste"
        @keydown="onHeadingKeydown"
        @click.stop="store.selectBlock(block.id)"
      />
      <div
        ref="subheadingRef"
        class="text-base outline-none leading-relaxed editable-placeholder"
        data-placeholder="Subheading…"
        :style="{ color: block.props.subheading_color, fontFamily: fontStack(block.props.font_family, 'Arial, Helvetica, sans-serif') }"
        contenteditable="true"
        @focus="onSubheadingFocus"
        @blur="onSubheadingBlur"
        @paste.prevent="onSubheadingPaste"
        @keydown="onSubheadingKeydown"
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
import { fontStack } from "../../fonts";

const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();
function update(key, val) { store.updateBlockProps(props.block.id, { [key]: val }); }

const blockProps = computed(() => props.block.props);
const paddingStyle = usePadding(blockProps, { top: 40, right: 16, bottom: 40, left: 16 });

const {
  elRef: headingRef,
  onFocus: onHeadingFocus, onBlur: onHeadingBlur,
  onPaste: onHeadingPaste, onKeydown: onHeadingKeydown,
} = useContentEditable(() => props.block.props.heading, (val) => update("heading", val));

const {
  elRef: subheadingRef,
  onFocus: onSubheadingFocus, onBlur: onSubheadingBlur,
  onPaste: onSubheadingPaste, onKeydown: onSubheadingKeydown,
} = useContentEditable(() => props.block.props.subheading, (val) => update("subheading", val));

const textAlignClass = computed(() => ({
  "text-left":   props.block.props.text_align === "left",
  "text-center": props.block.props.text_align === "center" || !props.block.props.text_align,
  "text-right":  props.block.props.text_align === "right",
}));
</script>
