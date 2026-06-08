<template>
  <BlockWrapper :block="block" :index="index">
    <div :class="alignClass" :style="paddingStyle">
      <!-- Line above -->
      <div
        v-if="block.props.line_position === 'above'"
        class="w-full mb-3"
        :style="{ borderTop: `1px solid ${block.props.line_color || '#ededed'}` }"
      />

      <!-- Label text -->
      <div
        class="inline-block tracking-widest uppercase outline-none"
        :style="{
          color: block.props.text_color || '#383838',
          fontSize: block.props.font_size || '11px',
          fontWeight: block.props.font_weight || '600',
          letterSpacing: '0.99px',
        }"
        contenteditable="true"
        @blur="update('label', $event.target.innerText)"
        @click.stop="store.selectBlock(block.id)"
      >{{ block.props.label }}</div>

      <!-- Line below -->
      <div
        v-if="block.props.line_position === 'below' || !block.props.line_position"
        class="w-full mt-3"
        :style="{ borderTop: `1px solid ${block.props.line_color || '#ededed'}` }"
      />
    </div>
  </BlockWrapper>
</template>

<script setup>
import { computed } from "vue";
import BlockWrapper from "../BlockWrapper.vue";
import { useEditorStore } from "../../stores/editor";
import { usePadding } from "../../composables/usePadding";

const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();
function update(key, val) { store.updateBlockProps(props.block.id, { [key]: val }); }

const blockProps = computed(() => props.block.props);
const paddingStyle = usePadding(blockProps, { top: 12, right: 32, bottom: 12, left: 32 });

const alignClass = computed(() => ({
  "text-left":   !props.block.props.align || props.block.props.align === "left",
  "text-center": props.block.props.align === "center",
  "text-right":  props.block.props.align === "right",
}));
</script>
