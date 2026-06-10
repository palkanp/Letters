<template>
  <aside
    class="flex-shrink-0 bg-white border-l border-gray-200 flex flex-col overflow-hidden"
    :style="{ width: (width || 288) + 'px' }"
  >

    <!-- Header -->
    <div class="px-4 py-3 border-b border-gray-200 flex items-center gap-2 min-h-[45px]">
      <template v-if="block">
        <FeatherIcon :name="schema.icon" class="w-4 h-4 text-gray-500 flex-shrink-0" />
        <span class="text-sm font-semibold text-gray-800">{{ schema.label }}</span>
      </template>
      <template v-else>
        <span class="text-xs font-semibold text-gray-400 uppercase tracking-widest">Properties</span>
      </template>
    </div>

    <!-- No selection empty state -->
    <div v-if="!block" class="flex-1 flex flex-col items-center justify-center px-6 text-center gap-3">
      <div class="w-12 h-12 rounded-xl bg-gray-100 flex items-center justify-center"><FeatherIcon name="layout" class="w-5 h-5 text-gray-400" /></div>
      <p class="text-sm text-gray-400 leading-relaxed">
        Click a block on the canvas to edit its properties here.
      </p>
    </div>

    <!-- Sections -->
    <div v-else class="flex-1 overflow-y-auto">

      <!-- Collapsible sections -->
      <div
        v-for="section in schema.sections"
        :key="section.id"
        class="border-b border-gray-100"
      >
        <!-- Section header -->
        <button
          type="button"
          class="w-full flex items-center justify-between px-4 py-2.5 text-left hover:bg-gray-50 transition-colors"
          @click="toggleSection(section.id)"
        >
          <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider">{{ section.title }}</span>
          <FeatherIcon
            name="chevron-down"
            class="w-3.5 h-3.5 text-gray-400 transition-transform duration-200"
            :class="openSections.has(section.id) ? 'rotate-0' : '-rotate-90'"
          />
        </button>

        <!-- Section fields -->
        <div v-show="openSections.has(section.id)" class="px-4 pb-4 pt-1 space-y-3">
          <div v-for="field in section.fields" :key="field.key">
            <label class="block text-xs font-medium text-gray-500 mb-1.5">{{ field.label }}</label>

            <!-- Color picker -->
            <div v-if="field.type === 'color'" class="flex items-center gap-2">
              <div class="relative w-9 h-9 flex-shrink-0">
                <input
                  type="color"
                  :value="value(field.key)"
                  @input="set(field.key, $event.target.value)"
                  class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <div
                  class="w-9 h-9 rounded-lg border-2 border-white shadow ring-1 ring-gray-200"
                  :style="{ backgroundColor: value(field.key) || '#ffffff' }"
                ></div>
              </div>
              <TextInput
                class="flex-1"
                size="sm"
                type="text"
                :modelValue="value(field.key)"
                @update:modelValue="set(field.key, $event)"
              />
            </div>

            <!-- Select — frappe-ui for string/number values -->
            <Select
              v-else-if="field.type === 'select' && !hasBooleanOptions(field)"
              :modelValue="value(field.key)"
              :options="field.options"
              size="sm"
              @update:modelValue="set(field.key, $event)"
            />
            <!-- Native select fallback for fields with boolean option values (e.g. show_dividers) -->
            <select
              v-else-if="field.type === 'select'"
              :value="value(field.key)"
              @change="set(field.key, coerce(field, $event.target.value))"
              class="w-full border border-gray-200 rounded-lg px-2.5 py-1.5 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-gray-300 appearance-none"
            >
              <option v-for="opt in field.options" :key="String(opt.value)" :value="opt.value">{{ opt.label }}</option>
            </select>

            <!-- Alignment segmented -->
            <div v-else-if="field.type === 'align'" class="flex rounded-lg border border-gray-200 overflow-hidden">
              <button
                v-for="opt in alignOptions"
                :key="opt.value"
                type="button"
                class="flex-1 py-2 text-xs font-semibold transition-colors"
                :class="value(field.key) === opt.value
                  ? 'bg-gray-900 text-white'
                  : 'bg-white text-gray-500 hover:bg-gray-50'"
                :title="opt.label"
                @click="set(field.key, opt.value)"
              ><FeatherIcon :name="opt.icon" class="w-3.5 h-3.5" /></button>
            </div>

            <!-- Number -->
            <div v-else-if="field.type === 'number'" class="flex items-center gap-2">
              <TextInput
                type="number"
                :min="field.min"
                :max="field.max"
                size="sm"
                :modelValue="value(field.key)"
                @update:modelValue="set(field.key, Number($event))"
              />
              <span v-if="field.unit" class="text-xs text-gray-400 flex-shrink-0">{{ field.unit }}</span>
            </div>

            <!-- Dimension (number + px/% unit toggle + auto reset) -->
            <div v-else-if="field.type === 'dimension'" class="flex items-center gap-1.5">
              <TextInput
                type="number"
                min="0"
                size="sm"
                class="flex-1 min-w-0"
                :modelValue="parseDimension(value(field.key)).num"
                @update:modelValue="set(field.key, $event + parseDimension(value(field.key)).unit)"
              />
              <div class="flex rounded-lg border border-gray-200 overflow-hidden flex-shrink-0">
                <button
                  v-for="u in ['px', '%']"
                  :key="u"
                  type="button"
                  class="px-2 py-1.5 text-xs font-semibold transition-colors"
                  :class="parseDimension(value(field.key)).unit === u
                    ? 'bg-gray-900 text-white'
                    : 'bg-white text-gray-500 hover:bg-gray-50'"
                  @click="set(field.key, parseDimension(value(field.key)).num + u)"
                >{{ u }}</button>
              </div>
              <!-- Auto reset: restores the "auto" keyword so CSS can take over -->
              <button
                type="button"
                class="px-2 py-1.5 text-xs font-semibold rounded-lg border border-gray-200 flex-shrink-0 transition-colors"
                :class="value(field.key) === 'auto'
                  ? 'bg-gray-900 text-white border-gray-900'
                  : 'bg-white text-gray-500 hover:bg-gray-50'"
                title="Set to auto (let content decide)"
                @click="set(field.key, 'auto')"
              >auto</button>
            </div>

            <!-- Text -->
            <TextInput
              v-else
              type="text"
              :placeholder="field.placeholder || ''"
              size="sm"
              :modelValue="value(field.key)"
              @update:modelValue="set(field.key, $event)"
            />
          </div>
        </div>
      </div>

      <!-- Universal Padding -->
      <div class="border-b border-gray-100">
        <button
          type="button"
          class="w-full flex items-center justify-between px-4 py-2.5 text-left hover:bg-gray-50 transition-colors"
          @click="toggleSection('__padding')"
        >
          <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider">Padding</span>
          <FeatherIcon
            name="chevron-down"
            class="w-3.5 h-3.5 text-gray-400 transition-transform duration-200"
            :class="openSections.has('__padding') ? 'rotate-0' : '-rotate-90'"
          />
        </button>
        <div v-show="openSections.has('__padding')" class="px-4 pb-4 pt-1 space-y-2">
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1.5">Top (px)</label>
              <TextInput type="number" size="sm" :min="0" :max="200"
                :modelValue="block.props.padding_top ?? 20"
                @update:modelValue="set('padding_top', Number($event))"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1.5">Bottom (px)</label>
              <TextInput type="number" size="sm" :min="0" :max="200"
                :modelValue="block.props.padding_bottom ?? 20"
                @update:modelValue="set('padding_bottom', Number($event))"
              />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1.5">Left (px)</label>
              <TextInput type="number" size="sm" :min="0" :max="200"
                :modelValue="block.props.padding_left ?? 32"
                @update:modelValue="set('padding_left', Number($event))"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1.5">Right (px)</label>
              <TextInput type="number" size="sm" :min="0" :max="200"
                :modelValue="block.props.padding_right ?? 32"
                @update:modelValue="set('padding_right', Number($event))"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Universal Spacing -->
      <div class="border-b border-gray-100">
        <button
          type="button"
          class="w-full flex items-center justify-between px-4 py-2.5 text-left hover:bg-gray-50 transition-colors"
          @click="toggleSection('__spacing')"
        >
          <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider">Spacing</span>
          <FeatherIcon
            name="chevron-down"
            class="w-3.5 h-3.5 text-gray-400 transition-transform duration-200"
            :class="openSections.has('__spacing') ? 'rotate-0' : '-rotate-90'"
          />
        </button>
        <div v-show="openSections.has('__spacing')" class="px-4 pb-4 pt-1 space-y-3">
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1.5">Top (px)</label>
              <TextInput type="number" size="sm" :min="0" :max="200"
                :modelValue="block.props.spacing_top ?? 4"
                @update:modelValue="set('spacing_top', Number($event))"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1.5">Bottom (px)</label>
              <TextInput type="number" size="sm" :min="0" :max="200"
                :modelValue="block.props.spacing_bottom ?? 4"
                @update:modelValue="set('spacing_bottom', Number($event))"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Block actions: Duplicate + Remove -->
      <div class="px-4 py-4 flex gap-2">
        <Button class="flex-1" @click="store.duplicateBlock(block.id)">
          <template #prefix><FeatherIcon name="copy" class="w-3.5 h-3.5" /></template>
          Duplicate
        </Button>
        <Button class="flex-1" theme="red" variant="subtle" @click="store.removeBlock(block.id)">
          <template #prefix><FeatherIcon name="trash-2" class="w-3.5 h-3.5" /></template>
          Remove
        </Button>
      </div>

    </div>
  </aside>
</template>

<script setup>
import { computed, reactive, watch } from "vue";
import { TextInput, Select, Button, FeatherIcon } from "frappe-ui";
import { useEditorStore } from "../stores/editor";
import { BLOCK_SCHEMA } from "../blockSchema";

defineProps({ width: { type: Number, default: 288 } });

const store = useEditorStore();
const block = computed(() => store.selectedBlock);
const schema = computed(() => (block.value ? BLOCK_SCHEMA[block.value.type] : null));

// Track which sections are open. Default all open.
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

const alignOptions = [
  { value: "left",   icon: "align-left",   label: "Left" },
  { value: "center", icon: "align-center", label: "Center" },
  { value: "right",  icon: "align-right",  label: "Right" },
];

function value(key) {
  return block.value?.props?.[key];
}

function set(key, val) {
  if (block.value) store.updateBlockProps(block.value.id, { [key]: val });
}

function coerce(field, raw) {
  const opt = field.options?.find((o) => String(o.value) === String(raw));
  return opt ? opt.value : raw;
}

// frappe-ui Select doesn't support boolean option values (SelectOptionValue = string | number | bigint | object).
// Fields with boolean options fall back to a native <select> + coerce().
function hasBooleanOptions(field) {
  return field.options?.some((o) => typeof o.value === "boolean") ?? false;
}

// Parse a CSS dimension string like "60%", "200px", "100%" into { num, unit }
// "auto" or missing → 0px (meaning "no constraint" for min-height, or 100% for width)
function parseDimension(val) {
  if (!val || val === "auto") return { num: 0, unit: "px" };
  const m = String(val).match(/^(\d*\.?\d+)(px|%)$/);
  if (m) return { num: parseFloat(m[1]), unit: m[2] };
  const n = parseFloat(val);
  return { num: isNaN(n) ? 0 : n, unit: val.includes("px") ? "px" : "%" };
}
</script>
