<template>
  <aside
    class="flex-shrink-0 bg-surface-base border-l border-outline-gray-1 flex flex-col overflow-hidden"
    :style="{ width: (width || 288) + 'px' }"
  >
    <!-- Header -->
    <div class="px-3 py-3 border-b border-outline-gray-1 flex items-center gap-2 min-h-[44px]">
      <template v-if="isMultiSelect">
        <span class="lucide-layers size-3.5 text-ink-gray-5 flex-shrink-0" aria-hidden="true" />
        <span class="text-sm font-medium text-ink-gray-8">{{ store.selectedBlockIds.size }} selected</span>
      </template>
      <template v-else-if="block">
        <span :class="`lucide-${schema?.icon || 'box'} size-3.5 text-ink-gray-5 flex-shrink-0`" aria-hidden="true" />
        <span class="text-sm font-medium text-ink-gray-8">{{ schema?.label || block.label || block.type }}</span>
        <template v-if="store.selectedSubLayerSection">
          <span class="text-ink-gray-4 text-sm">/</span>
          <span class="text-sm font-medium text-ink-gray-6">
            {{ schema?.sub_layers?.find(sl => sl.section === store.selectedSubLayerSection)?.label }}
          </span>
        </template>
      </template>
      <template v-else>
        <span class="lucide-mail size-3.5 text-ink-gray-5 flex-shrink-0" aria-hidden="true" />
        <span class="text-sm font-medium text-ink-gray-8">Body</span>
      </template>
    </div>

    <!-- Multi-select state -->
    <div v-if="isMultiSelect" class="flex-1 flex flex-col">
      <div class="flex-1 flex flex-col items-center justify-center px-4 gap-2 text-center">
        <span class="lucide-layers size-8 text-ink-gray-3" aria-hidden="true" />
        <p class="text-sm text-ink-gray-5">{{ store.selectedBlockIds.size }} blocks selected</p>
        <p class="text-xs text-ink-gray-4">Cmd+C to copy · Cmd+V to paste</p>
      </div>
      <div class="px-3 py-4 border-t border-outline-gray-1 flex gap-2">
        <Button class="flex-1" size="sm" theme="red" variant="outline" @click="deleteSelected">
          <template #prefix><span class="lucide-trash-2 size-3.5" aria-hidden="true" /></template>
          Delete all
        </Button>
      </div>
    </div>

    <!-- Canvas (body) properties — shown when nothing is selected -->
    <div v-else-if="!block" class="flex-1 overflow-y-auto">
      <div class="border-b border-outline-gray-1">
        <Button
          variant="ghost"
          class="w-full justify-between px-3 py-2.5"
          @click="canvasOpen = !canvasOpen"
        >
          <span class="text-xs font-semibold text-ink-gray-9">Canvas</span>
          <template #suffix>
            <span
              class="lucide-chevron-down size-3.5 text-ink-gray-4 transition-transform duration-150"
              :class="canvasOpen ? '' : '-rotate-90'"
              aria-hidden="true"
            />
          </template>
        </Button>
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
    <div v-else-if="block" class="flex-1 overflow-y-auto">

      <!-- Schema-defined sections (filtered to active sub-layer if one is selected) -->
      <div
        v-for="section in (schema?.sections ?? []).filter(s => !store.selectedSubLayerSection || s.id === store.selectedSubLayerSection)"
        :key="section.id"
        class="border-b border-outline-gray-1"
      >
        <Button
          variant="ghost"
          class="w-full justify-between px-3 py-2.5"
          @click="toggleSection(section.id)"
        >
          <span class="text-xs font-semibold text-ink-gray-9">{{ section.title }}</span>
          <template #suffix>
            <span
              class="lucide-chevron-down size-3.5 text-ink-gray-4 transition-transform duration-150"
              :class="openSections.has(section.id) ? '' : '-rotate-90'"
              aria-hidden="true"
            />
          </template>
        </Button>
        <div v-show="openSections.has(section.id)" class="px-3 pb-4 flex flex-col gap-2">
          <PropRow
            v-for="field in section.fields.filter(f => !f.showWhen || f.showWhen(block?.props))"
            :key="field.key"
            :label="field.label"
            :hint="field.hint"
          >
            <FieldControl :field="field" :value="value(field.key)" :block-props="block?.props" @change="set(field.key, $event)" />
          </PropRow>
        </div>
      </div>

      <!-- Size — hidden for types that control their own dimensions in schema sections -->
      <div v-if="!['container', 'image', 'spacer', 'divider'].includes(block.type)" class="border-b border-outline-gray-1">
        <Button
          variant="ghost"
          class="w-full justify-between px-3 py-2.5"
          @click="toggleSection('__size')"
        >
          <span class="text-xs font-semibold text-ink-gray-9">Size</span>
          <template #suffix>
            <span
              class="lucide-chevron-down size-3.5 text-ink-gray-4 transition-transform duration-150"
              :class="openSections.has('__size') ? '' : '-rotate-90'"
              aria-hidden="true"
            />
          </template>
        </Button>
        <div v-show="openSections.has('__size')" class="px-3 pb-4 flex flex-col gap-0">
          <PropRow label="Width">
            <TextInput type="text" size="sm" placeholder="auto"
              :modelValue="block.props.block_width ?? ''"
              @update:modelValue="set('block_width', $event || undefined)"
            />
          </PropRow>
          <PropRow label="Height">
            <TextInput type="text" size="sm" placeholder="auto"
              :modelValue="block.props.block_height ?? ''"
              @update:modelValue="set('block_height', $event || undefined)"
            />
          </PropRow>
        </div>
      </div>

      <!-- Padding & Spacing -->
      <div class="border-b border-outline-gray-1">
        <Button
          variant="ghost"
          class="w-full justify-between px-3 py-2.5"
          @click="toggleSection('__spacing')"
        >
          <span class="text-xs font-semibold text-ink-gray-9">Spacing</span>
          <template #suffix>
            <span
              class="lucide-chevron-down size-3.5 text-ink-gray-4 transition-transform duration-150"
              :class="openSections.has('__spacing') ? '' : '-rotate-90'"
              aria-hidden="true"
            />
          </template>
        </Button>
        <div v-show="openSections.has('__spacing')" class="px-3 pb-4 flex flex-col gap-0">
          <PropRow label="Padding">
            <div @focusout.stop="commitPadding">
              <TextInput
                type="text" size="sm" placeholder="20px 16px"
                :modelValue="localPadding"
                @update:modelValue="localPadding = $event"
                @keydown.enter.prevent="commitPadding"
              />
            </div>
          </PropRow>
          <PropRow label="Margin">
            <div @focusout.stop="commitSpacing">
              <TextInput
                type="text" size="sm" placeholder="4px 0px"
                :modelValue="localSpacing"
                @update:modelValue="localSpacing = $event"
                @keydown.enter.prevent="commitSpacing"
              />
            </div>
          </PropRow>
        </div>
      </div>

    </div>
  </aside>
</template>

<script setup>
import { computed, nextTick, reactive, ref, watch } from "vue";
import { TextInput, Button, Slider } from "frappe-ui";
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
const isMultiSelect = computed(() => store.selectedBlockIds.size > 1);

function deleteSelected() {
  const ids = [...store.selectedBlockIds];
  ids.forEach((id) => store.removeBlock(id));
}

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
      openSections.add("__spacing");
    }
  },
  { immediate: true }
);
function toggleSection(id) {
  if (openSections.has(id)) openSections.delete(id);
  else openSections.add(id);
}

const PADDING_DEFAULTS = { top: 20, right: 16, bottom: 20, left: 16 };
const SPACING_DEFAULTS = { top: 4, right: 0, bottom: 4, left: 0 };

function getBoxShorthand(props, prefix, defaults) {
  const t = props[`${prefix}_top`]    ?? defaults.top;
  const r = props[`${prefix}_right`]  ?? defaults.right;
  const b = props[`${prefix}_bottom`] ?? defaults.bottom;
  const l = props[`${prefix}_left`]   ?? defaults.left;
  if (t === r && r === b && b === l) return `${t}px`;
  if (t === b && r === l) return `${t}px ${r}px`;
  return `${t}px ${r}px ${b}px ${l}px`;
}

function setBoxShorthand(value, prefix) {
  if (!block.value) return;
  const parts = String(value).trim().split(/\s+/).map(v => parseInt(v, 10)).filter(n => !isNaN(n));
  if (!parts.length) return;
  let t, r, b, l;
  if (parts.length === 1)      { [t, r, b, l] = [parts[0], parts[0], parts[0], parts[0]]; }
  else if (parts.length === 2) { [t, r, b, l] = [parts[0], parts[1], parts[0], parts[1]]; }
  else if (parts.length === 3) { [t, r, b, l] = [parts[0], parts[1], parts[2], parts[1]]; }
  else                         { [t, r, b, l] = parts; }
  store.updateBlockProps(block.value.id, {
    [`${prefix}_top`]: t, [`${prefix}_right`]: r,
    [`${prefix}_bottom`]: b, [`${prefix}_left`]: l,
  });
}

// Local refs for in-progress editing — only commit on blur/Enter to avoid cursor jumps
const localPadding = ref("");
const localSpacing = ref("");

watch(
  () => block.value?.id,
  () => {
    localPadding.value = block.value ? getBoxShorthand(block.value.props, "padding", PADDING_DEFAULTS) : "";
    localSpacing.value = block.value ? getBoxShorthand(block.value.props, "spacing", SPACING_DEFAULTS) : "";
  },
  { immediate: true },
);

function commitPadding() {
  setBoxShorthand(localPadding.value, "padding");
  nextTick(() => {
    if (block.value) localPadding.value = getBoxShorthand(block.value.props, "padding", PADDING_DEFAULTS);
  });
}
function commitSpacing() {
  setBoxShorthand(localSpacing.value, "spacing");
  nextTick(() => {
    if (block.value) localSpacing.value = getBoxShorthand(block.value.props, "spacing", SPACING_DEFAULTS);
  });
}

function value(key) { return block.value?.props?.[key]; }
function set(key, val) {
  if (!block.value) return;
  const updates = { [key]: val };
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
