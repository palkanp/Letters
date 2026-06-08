<template>
  <BlockWrapper :block="block" :index="index">
    <div class="px-8 py-5">
      <div
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
        @blur="update('content', $event.target.innerText)"
        @click.stop="store.selectBlock(block.id)"
      >{{ block.props.content }}</div>
    </div>
  </BlockWrapper>
</template>

<script setup>
import { computed } from "vue";
import BlockWrapper from "../BlockWrapper.vue";
import { useEditorStore } from "../../stores/editor";
const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();
function update(key, val) { store.updateBlockProps(props.block.id, { [key]: val }); }

const alignClass = computed(() => ({
  "text-left":   props.block.props.align === "left" || !props.block.props.align,
  "text-center": props.block.props.align === "center",
  "text-right":  props.block.props.align === "right",
}));
</script>
