<template>
  <BlockWrapper :block="block" :index="index">
    <div :style="{ backgroundColor: block.props.background_color || '#ffffff', fontFamily: fontStack(block.props.font_family, 'Arial, Helvetica, sans-serif'), ...paddingStyle }">

      <!-- Optional section heading -->
      <EditableDiv
        v-if="block.props.heading !== undefined"
        class="font-semibold mb-3 outline-none text-sm uppercase tracking-wide"
        :style="{ color: '#374151' }"
        :model-value="block.props.heading || ''"
        placeholder="Optional heading..."
        @update:model-value="update('heading', $event)"
        @click.stop="store.selectBlock(block.id)"
      />

      <!-- Items -->
      <div class="space-y-2.5">
        <div
          v-for="(item, i) in items"
          :key="i"
          class="group/item flex items-start gap-2"
          @click.stop="store.selectBlock(block.id)"
        >
          <!-- Marker -->
          <span
            v-if="block.props.style !== 'none'"
            class="flex-shrink-0 mt-0.5 w-4 text-sm leading-snug select-none"
            :style="{ color: block.props.accent_color || '#9ca3af' }"
          >
            {{ block.props.style === 'numbered' ? (i + 1) + '.' : '•' }}
          </span>

          <!-- Content -->
          <div class="flex-1 min-w-0">
            <!-- Title row -->
            <div class="flex items-center gap-2 flex-wrap">
              <EditableDiv
                class="font-medium text-sm outline-none leading-snug"
                :style="{ color: block.props.link_color || '#2563eb', textDecoration: 'underline' }"
                :model-value="item.title || ''"
                placeholder="Link title..."
                @update:model-value="updateItem(i, 'title', $event)"
                @click.stop="store.selectBlock(block.id)"
              />
              <!-- URL input (only when selected) -->
              <div v-if="isSelected" class="flex items-center gap-1 min-w-0">
                <FeatherIcon name="link" class="w-3 h-3 text-gray-300 flex-shrink-0" />
                <input
                  type="text"
                  :value="item.url || ''"
                  placeholder="https://example.com"
                  class="text-xs text-gray-400 bg-transparent border-0 border-b border-dashed
                         border-gray-200 outline-none w-44 focus:border-gray-400 focus:text-gray-600"
                  @input="updateItem(i, 'url', $event.target.value)"
                  @click.stop
                />
              </div>
            </div>

            <!-- Description (optional) -->
            <EditableDiv
              v-if="item.description !== undefined"
              class="text-xs mt-0.5 outline-none leading-relaxed"
              :style="{ color: block.props.text_color || '#6b7280' }"
              :model-value="item.description || ''"
              placeholder="Optional description..."
              @update:model-value="updateItem(i, 'description', $event)"
              @click.stop="store.selectBlock(block.id)"
            />
          </div>

          <!-- Remove item (when block selected) -->
          <button
            v-if="isSelected"
            type="button"
            title="Remove item"
            class="flex-shrink-0 opacity-0 group-hover/item:opacity-100 transition-opacity
                   text-gray-300 hover:text-red-400"
            @click.stop="removeItem(i)"
          >
            <FeatherIcon name="x" class="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <!-- Add item button (when selected) -->
      <button
        v-if="isSelected"
        type="button"
        class="mt-3 flex items-center gap-1 text-xs text-gray-400 hover:text-gray-700 transition-colors"
        @click.stop="addItem"
      >
        <FeatherIcon name="plus" class="w-3 h-3" /> Add item
      </button>
    </div>
  </BlockWrapper>
</template>

<script setup>
import { computed } from "vue";
import { FeatherIcon } from "frappe-ui";
import BlockWrapper from "../BlockWrapper.vue";
import EditableDiv from "../EditableDiv.vue";
import { useEditorStore } from "../../stores/editor";
import { usePadding } from "../../composables/usePadding";
import { fontStack } from "../../fonts";

const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();
function update(key, val) { store.updateBlockProps(props.block.id, { [key]: val }); }

const blockProps   = computed(() => props.block.props);
const paddingStyle = usePadding(blockProps, { top: 20, right: 16, bottom: 20, left: 16 });

const isSelected = computed(() => store.selectedBlockId === props.block.id);

// Items as a computed copy (never mutate props directly)
const items = computed(() => props.block.props.items || []);

function updateItem(index, key, value) {
  const newItems = items.value.map((item, i) =>
    i === index ? { ...item, [key]: value } : item
  );
  update("items", newItems);
}

function addItem() {
  const newItems = [
    ...items.value,
    { title: "New item", url: "https://example.com", description: "" },
  ];
  update("items", newItems);
}

function removeItem(index) {
  const newItems = items.value.filter((_, i) => i !== index);
  update("items", newItems);
}
</script>
