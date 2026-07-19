<template>
  <BlockWrapper :block="block" :index="index">
    <div
      class="text-center"
      :style="{ backgroundColor: block.props.background_color, ...paddingStyle }"
    >
      <div
        ref="textRef"
        class="text-xs leading-relaxed outline-none"
        :style="{ color: block.props.text_color, fontFamily: fontStack(block.props.font_family, 'Arial, Helvetica, sans-serif') }"
        contenteditable="true"
        @focus="onFocus"
        @blur="onBlur"
        @paste.prevent="onPaste"
        @keydown="onKeydown"
        @click.stop="store.selectBlock(block.id)"
      />

      <!-- Service / compliance links (unsubscribe, preferences…) -->
      <div
        v-if="links.length || isSelected"
        class="mt-2 flex items-center justify-center gap-1.5 flex-wrap"
        @click.stop="store.selectBlock(block.id)"
      >
        <template v-for="(link, i) in links" :key="i">
          <span
            v-if="i > 0"
            class="text-xs select-none"
            :style="{ color: block.props.text_color }"
          >·</span>
          <span class="inline-flex items-center gap-1 group/link min-w-0">
            <EditableDiv
              class="text-xs underline outline-none whitespace-nowrap"
              :style="{ color: linkColor, fontFamily: fontStack(block.props.font_family, 'Arial, Helvetica, sans-serif') }"
              :model-value="link.label || ''"
              placeholder="Link label..."
              @update:model-value="updateLink(i, 'label', $event)"
              @click.stop="store.selectBlock(block.id)"
            />
            <template v-if="isSelected">
              <TextInput
                type="text"
                size="sm"
                class="w-40 min-w-0"
                :modelValue="link.url || ''"
                placeholder="https://example.com"
                @update:modelValue="updateLink(i, 'url', $event)"
                @click.stop
              />
              <Button
                variant="ghost"
                icon="lucide-x"
                size="sm"
                title="Remove link"
                class="flex-shrink-0 opacity-0 group-hover/link:opacity-100 transition-opacity"
                @click.stop="removeLink(i)"
              />
            </template>
          </span>
        </template>

        <Button
          v-if="isSelected"
          variant="ghost"
          size="sm"
          class="text-ink-gray-4 hover:text-ink-gray-7"
          iconLeft="lucide-plus"
          @click.stop="addLink"
        >
          Link
        </Button>
      </div>
    </div>
  </BlockWrapper>
</template>

<script setup>
import { computed } from "vue";
import { Button, TextInput } from "frappe-ui";
import BlockWrapper from "../BlockWrapper.vue";
import EditableDiv from "../EditableDiv.vue";
import { useEditorStore } from "../../stores/editor";
import { usePadding } from "../../composables/usePadding";
import { useContentEditable } from "../../composables/useContentEditable";
import { fontStack } from "../../fonts";

const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();
function update(key, val) { store.updateBlockProps(props.block.id, { [key]: val }); }

const blockProps = computed(() => props.block.props);
const paddingStyle = usePadding(blockProps);

const links      = computed(() => props.block.props.links || []);
const isSelected = computed(() => store.selectedBlockId === props.block.id);
const linkColor  = computed(() => props.block.props.link_color || props.block.props.text_color || "#6b7280");

function updateLink(i, key, val) {
  update("links", links.value.map((l, j) => (j === i ? { ...l, [key]: val } : l)));
}
function addLink() {
  update("links", [...links.value, { label: "New link", url: "https://example.com" }]);
}
function removeLink(i) {
  update("links", links.value.filter((_, j) => j !== i));
}

const { elRef: textRef, onFocus, onBlur, onPaste, onKeydown } = useContentEditable(
  () => props.block.props.text,
  (val) => update("text", val)
);
</script>
