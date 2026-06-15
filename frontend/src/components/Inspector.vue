<template>
  <aside
    class="flex-shrink-0 bg-surface-base border-l border-outline-gray-1 flex flex-col overflow-hidden"
    :style="{ width: (width || 288) + 'px' }"
  >
    <!-- Header -->
    <div class="px-3 py-3 border-b border-outline-gray-1 flex items-center gap-2 min-h-[44px]">
      <template v-if="block">
        <FeatherIcon :name="schema.icon" class="w-3.5 h-3.5 text-ink-gray-5 flex-shrink-0" />
        <span class="text-sm font-medium text-ink-gray-8">{{ schema.label }}</span>
      </template>
      <template v-else>
        <FeatherIcon name="mail" class="w-3.5 h-3.5 text-ink-gray-5 flex-shrink-0" />
        <span class="text-sm font-medium text-ink-gray-8">Body</span>
      </template>
    </div>

    <!-- Canvas (body) properties — shown when nothing is selected -->
    <div v-if="!block" class="flex-1 overflow-y-auto">
      <div class="border-b border-outline-gray-1">
        <button
          type="button"
          class="w-full flex items-center justify-between px-3 py-2.5 text-left hover:bg-surface-gray-2 transition-colors"
          @click="canvasOpen = !canvasOpen"
        >
          <span class="text-xs font-semibold text-ink-gray-9">Canvas</span>
          <FeatherIcon
            name="chevron-down"
            class="w-3.5 h-3.5 text-ink-gray-4 transition-transform duration-150"
            :class="canvasOpen ? '' : '-rotate-90'"
          />
        </button>
        <div v-show="canvasOpen" class="px-3 pb-4 flex flex-col gap-2">
          <div class="flex items-center gap-2 py-1">
            <span class="w-24 shrink-0 text-xs text-ink-gray-5">Width</span>
            <div class="flex-1 min-w-0 flex items-center gap-2">
              <Slider
                :modelValue="[store.emailWidth]"
                :min="320"
                :max="900"
                :step="10"
                size="sm"
                class="flex-1"
                @update:modelValue="(arr) => setEmailWidth(arr[0])"
              />
              <span class="text-xs text-ink-gray-5 w-10 text-right flex-shrink-0 tabular-nums">{{ store.emailWidth }}px</span>
            </div>
          </div>
          <div class="flex items-center gap-2 py-1">
            <span class="w-24 shrink-0 text-xs text-ink-gray-5">Canvas BG</span>
            <div class="flex-1 min-w-0">
              <ColorPicker
                :model-value="store.canvasBg"
                @update:model-value="(v) => { store.canvasBg = v; store.markDirty(); }"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Block sections -->
    <div v-else class="flex-1 overflow-y-auto">

      <!-- Schema-defined sections -->
      <div
        v-for="section in schema.sections"
        :key="section.id"
        class="border-b border-outline-gray-1"
      >
        <button
          type="button"
          class="w-full flex items-center justify-between px-3 py-2.5 text-left hover:bg-surface-gray-2 transition-colors"
          @click="toggleSection(section.id)"
        >
          <span class="text-xs font-semibold text-ink-gray-9">{{ section.title }}</span>
          <FeatherIcon
            name="chevron-down"
            class="w-3.5 h-3.5 text-ink-gray-4 transition-transform duration-150"
            :class="openSections.has(section.id) ? '' : '-rotate-90'"
          />
        </button>
        <div v-show="openSections.has(section.id)" class="px-3 pb-4 flex flex-col gap-2">
          <PropRow
            v-for="field in section.fields"
            :key="field.key"
            :label="field.label"
            :hint="field.hint"
          >
            <FieldControl :field="field" :value="value(field.key)" :block-props="block?.props" @change="set(field.key, $event)" />
          </PropRow>
        </div>
      </div>

      <!-- Padding -->
      <div class="border-b border-outline-gray-1">
        <button
          type="button"
          class="w-full flex items-center justify-between px-3 py-2.5 text-left hover:bg-surface-gray-2 transition-colors"
          @click="toggleSection('__padding')"
        >
          <span class="text-xs font-semibold text-ink-gray-9">Padding</span>
          <FeatherIcon
            name="chevron-down"
            class="w-3.5 h-3.5 text-ink-gray-4 transition-transform duration-150"
            :class="openSections.has('__padding') ? '' : '-rotate-90'"
          />
        </button>
        <div v-show="openSections.has('__padding')" class="px-3 pb-4">
          <div class="grid grid-cols-2 gap-x-2 gap-y-1">
            <PropRow label="Top" compact>
              <TextInput type="number" size="sm" :min="0" :max="200"
                :modelValue="block.props.padding_top ?? 20"
                @update:modelValue="set('padding_top', Number($event))"
              />
            </PropRow>
            <PropRow label="Bottom" compact>
              <TextInput type="number" size="sm" :min="0" :max="200"
                :modelValue="block.props.padding_bottom ?? 20"
                @update:modelValue="set('padding_bottom', Number($event))"
              />
            </PropRow>
            <PropRow label="Left" compact>
              <TextInput type="number" size="sm" :min="0" :max="200"
                :modelValue="block.props.padding_left ?? 16"
                @update:modelValue="set('padding_left', Number($event))"
              />
            </PropRow>
            <PropRow label="Right" compact>
              <TextInput type="number" size="sm" :min="0" :max="200"
                :modelValue="block.props.padding_right ?? 16"
                @update:modelValue="set('padding_right', Number($event))"
              />
            </PropRow>
          </div>
        </div>
      </div>

      <!-- Spacing -->
      <div class="border-b border-outline-gray-1">
        <button
          type="button"
          class="w-full flex items-center justify-between px-3 py-2.5 text-left hover:bg-surface-gray-2 transition-colors"
          @click="toggleSection('__spacing')"
        >
          <span class="text-xs font-semibold text-ink-gray-9">Spacing</span>
          <FeatherIcon
            name="chevron-down"
            class="w-3.5 h-3.5 text-ink-gray-4 transition-transform duration-150"
            :class="openSections.has('__spacing') ? '' : '-rotate-90'"
          />
        </button>
        <div v-show="openSections.has('__spacing')" class="px-3 pb-4">
          <div class="grid grid-cols-2 gap-x-2 gap-y-1">
            <PropRow label="Top" compact>
              <TextInput type="number" size="sm" :min="0" :max="200"
                :modelValue="block.props.spacing_top ?? 4"
                @update:modelValue="set('spacing_top', Number($event))"
              />
            </PropRow>
            <PropRow label="Bottom" compact>
              <TextInput type="number" size="sm" :min="0" :max="200"
                :modelValue="block.props.spacing_bottom ?? 4"
                @update:modelValue="set('spacing_bottom', Number($event))"
              />
            </PropRow>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="px-3 py-4 flex gap-2">
        <Button class="flex-1" size="sm" variant="outline" @click="store.duplicateBlock(block.id)">
          <template #prefix><FeatherIcon name="copy" class="w-3.5 h-3.5" /></template>
          Duplicate
        </Button>
        <Button class="flex-1" size="sm" theme="red" variant="outline" @click="store.removeBlock(block.id)">
          <template #prefix><FeatherIcon name="trash-2" class="w-3.5 h-3.5" /></template>
          Remove
        </Button>
      </div>

    </div>
  </aside>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { TextInput, Button, FeatherIcon, Slider } from "frappe-ui";
import ColorPicker from "./ColorPicker.vue";
import FieldControl from "./FieldControl.vue";
import PropRow from "./PropRow.vue";
import { useEditorStore } from "../stores/editor";
import { BLOCK_SCHEMA } from "../blockSchema";
import { fontWeightOptions } from "../fonts";

defineProps({ width: { type: Number, default: 288 } });

const store = useEditorStore();
const block = computed(() => store.selectedBlock);
const canvasOpen = ref(true);
const schema = computed(() => (block.value ? BLOCK_SCHEMA[block.value.type] : null));

function setEmailWidth(w) {
  if (!isNaN(w) && w >= 320 && w <= 900) {
    store.emailWidth = w;
    store.markDirty();
  }
}

const openSections = reactive(new Set());
watch(
  () => block.value?.type,
  (type) => {
    openSections.clear();
    if (type && BLOCK_SCHEMA[type]) {
      BLOCK_SCHEMA[type].sections.forEach((s) => openSections.add(s.id));
      openSections.add("__padding");
      openSections.add("__spacing");
    }
  },
  { immediate: true }
);
function toggleSection(id) {
  if (openSections.has(id)) openSections.delete(id);
  else openSections.add(id);
}

function value(key) { return block.value?.props?.[key]; }
function set(key, val) {
  if (!block.value) return;
  const updates = { [key]: val };
  // When the font changes, clamp font_weight to a value the new font supports.
  if (key === "font_family") {
    const opts = fontWeightOptions(val);
    const validWeights = new Set(opts.map(o => o.value));
    const current = block.value.props?.font_weight;
    if (current && !validWeights.has(current)) {
      updates.font_weight = validWeights.has("400") ? "400" : opts[0].value;
    }
  }
  store.updateBlockProps(block.value.id, updates);
}
</script>
