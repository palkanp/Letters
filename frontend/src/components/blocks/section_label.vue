<template>
  <BlockWrapper :block="block" :index="index">
    <div class="px-8 py-3" :class="alignClass">
      <!-- Line above -->
      <div
        v-if="block.props.line_position === 'above'"
        class="w-full mb-3"
        :style="{ borderTop: `1px solid ${block.props.line_color || '#ededed'}` }"
      />

      <!-- Label text -->
      <div
        class="inline-block text-xs font-semibold tracking-widest uppercase outline-none"
        :style="{ color: block.props.text_color || '#383838', letterSpacing: '0.99px' }"
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

const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();
function update(key, val) { store.updateBlockProps(props.block.id, { [key]: val }); }

const alignClass = computed(() => ({
  "text-left":   !props.block.props.align || props.block.props.align === "left",
  "text-center": props.block.props.align === "center",
  "text-right":  props.block.props.align === "right",
}));
</script>
