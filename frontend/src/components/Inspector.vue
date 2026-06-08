<template>
  <aside class="w-72 flex-shrink-0 bg-white border-l border-gray-200 flex flex-col overflow-hidden">

    <!-- Header -->
    <div class="px-4 py-3 border-b border-gray-200 flex items-center gap-2 min-h-[45px]">
      <template v-if="block">
        <span class="text-base leading-none">{{ schema.icon }}</span>
        <span class="text-sm font-semibold text-gray-800">{{ schema.label }}</span>
      </template>
      <template v-else>
        <span class="text-xs font-semibold text-gray-400 uppercase tracking-widest">Properties</span>
      </template>
    </div>

    <!-- No selection empty state -->
    <div v-if="!block" class="flex-1 flex flex-col items-center justify-center px-6 text-center gap-3">
      <div class="w-12 h-12 rounded-xl bg-gray-100 flex items-center justify-center text-2xl">✦</div>
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
          <span
            class="text-gray-400 text-xs transition-transform duration-200"
            :class="openSections.has(section.id) ? 'rotate-0' : '-rotate-90'"
          >▾</span>
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
              <input
                type="text"
                :value="value(field.key)"
                @change="set(field.key, $event.target.value)"
                class="flex-1 border border-gray-200 rounded-lg px-2.5 py-1.5 text-sm text-gray-700 font-mono uppercase focus:outline-none focus:ring-2 focus:ring-gray-300"
                maxlength="7"
              />
            </div>

            <!-- Select -->
            <select
              v-else-if="field.type === 'select'"
              :value="value(field.key)"
              @change="set(field.key, coerce(field, $event.target.value))"
              class="w-full border border-gray-200 rounded-lg px-2.5 py-1.5 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-gray-300 appearance-none"
            >
              <option v-for="opt in field.options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
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
              >{{ opt.label }}</button>
            </div>

            <!-- Number -->
            <div v-else-if="field.type === 'number'" class="flex items-center gap-2">
              <input
                type="number"
                :min="field.min"
                :max="field.max"
                :value="value(field.key)"
                @input="set(field.key, Number($event.target.value))"
                class="w-full border border-gray-200 rounded-lg px-2.5 py-1.5 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-300"
              />
              <span v-if="field.unit" class="text-xs text-gray-400 flex-shrink-0">{{ field.unit }}</span>
            </div>

            <!-- Text -->
            <input
              v-else
              type="text"
              :placeholder="field.placeholder || ''"
              :value="value(field.key)"
              @change="set(field.key, $event.target.value)"
              class="w-full border border-gray-200 rounded-lg px-2.5 py-1.5 text-sm text-gray-700 placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-300"
            />
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
          <span
            class="text-gray-400 text-xs transition-transform duration-200"
            :class="openSections.has('__spacing') ? 'rotate-0' : '-rotate-90'"
          >▾</span>
        </button>
        <div v-show="openSections.has('__spacing')" class="px-4 pb-4 pt-1 space-y-3">
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1.5">Top (px)</label>
              <input
                type="number" min="0" max="200"
                :value="block.props.spacing_top ?? 4"
                @input="set('spacing_top', Number($event.target.value))"
                class="w-full border border-gray-200 rounded-lg px-2.5 py-1.5 text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-300"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1.5">Bottom (px)</label>
              <input
                type="number" min="0" max="200"
                :value="block.props.spacing_bottom ?? 4"
                @input="set('spacing_bottom', Number($event.target.value))"
                class="w-full border border-gray-200 rounded-lg px-2.5 py-1.5 text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-300"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Delete block -->
      <div class="px-4 py-4">
        <button
          type="button"
          class="w-full flex items-center justify-center gap-1.5 text-sm text-red-500 hover:text-red-600 hover:bg-red-50 rounded-lg py-2 transition-colors border border-transparent hover:border-red-100"
          @click="store.removeBlock(block.id)"
        >
          <span class="text-base leading-none">✕</span>
          <span>Remove block</span>
        </button>
      </div>

    </div>
  </aside>
</template>

<script setup>
import { computed, reactive, watch } from "vue";
import { useEditorStore } from "../stores/editor";
import { BLOCK_SCHEMA } from "../blockSchema";

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
    }
  },
  { immediate: true }
);

function toggleSection(id) {
  if (openSections.has(id)) openSections.delete(id);
  else openSections.add(id);
}

const alignOptions = [
  { value: "left",   icon: "←", label: "Left" },
  { value: "center", icon: "↔", label: "Center" },
  { value: "right",  icon: "→", label: "Right" },
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
</script>
