<template>
  <BlockWrapper :block="block" :index="index">
    <div :style="{ backgroundColor: block.props.background_color, ...paddingStyle }">

      <!-- Left-border style -->
      <template v-if="block.props.style !== 'centered'">
        <div :style="leftBorderStyle" class="pl-5">
          <div
            class="outline-none text-base italic leading-relaxed mb-3"
            :style="{ color: block.props.quote_color }"
            contenteditable="true"
            @blur="update('quote', $event.target.innerText)"
            @click.stop="store.selectBlock(block.id)"
          >{{ block.props.quote }}</div>
          <div
            class="text-sm font-semibold outline-none"
            :style="{ color: block.props.author_color }"
            contenteditable="true"
            @blur="update('author', $event.target.innerText)"
            @click.stop="store.selectBlock(block.id)"
          >{{ block.props.author }}</div>
          <div
            class="text-xs outline-none mt-0.5"
            :style="{ color: block.props.author_color }"
            contenteditable="true"
            @blur="update('role', $event.target.innerText)"
            @click.stop="store.selectBlock(block.id)"
          >{{ block.props.role }}</div>
        </div>
      </template>

      <!-- Centered / big-quote style -->
      <template v-else>
        <div class="text-center">
          <div class="text-5xl leading-none mb-2 select-none" :style="{ color: block.props.border_color }">&#8220;</div>
          <div
            class="outline-none text-base italic leading-relaxed mb-4 max-w-lg mx-auto"
            :style="{ color: block.props.quote_color }"
            contenteditable="true"
            @blur="update('quote', $event.target.innerText)"
            @click.stop="store.selectBlock(block.id)"
          >{{ block.props.quote }}</div>
          <div
            class="text-sm font-semibold outline-none"
            :style="{ color: block.props.author_color }"
            contenteditable="true"
            @blur="update('author', $event.target.innerText)"
            @click.stop="store.selectBlock(block.id)"
          >{{ block.props.author }}</div>
          <div
            class="text-xs outline-none mt-0.5"
            :style="{ color: block.props.author_color }"
            contenteditable="true"
            @blur="update('role', $event.target.innerText)"
            @click.stop="store.selectBlock(block.id)"
          >{{ block.props.role }}</div>
        </div>
      </template>

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
const paddingStyle = usePadding(blockProps);

const leftBorderStyle = computed(() => ({
  borderLeft: `4px solid ${props.block.props.border_color || "#e5e7eb"}`,
}));
</script>
