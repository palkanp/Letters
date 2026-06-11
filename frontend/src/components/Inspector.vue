<template>
  <aside
    class="flex-shrink-0 bg-white border-l border-gray-200 flex flex-col overflow-hidden"
    :style="{ width: (width || 288) + 'px' }"
  >
    <!-- Header -->
    <div class="px-3 py-2 border-b border-outline-gray-1 flex items-center gap-2 min-h-[40px]">
      <template v-if="block">
        <FeatherIcon :name="schema.icon" class="w-3.5 h-3.5 text-ink-gray-5 flex-shrink-0" />
        <span class="text-sm font-medium text-ink-gray-8">{{ schema.label }}</span>
      </template>
      <template v-else>
        <span class="text-xs text-ink-gray-4 font-medium uppercase tracking-widest">Properties</span>
      </template>
    </div>

    <!-- No selection empty state -->
    <div v-if="!block" class="flex-1 flex flex-col items-center justify-center px-6 text-center gap-3">
      <div class="w-10 h-10 rounded-xl bg-surface-gray-2 flex items-center justify-center">
        <FeatherIcon name="layout" class="w-4 h-4 text-ink-gray-4" />
      </div>
      <p class="text-sm text-ink-gray-4 leading-relaxed">
        Click a block to edit its properties.
      </p>
    </div>

    <!-- Sections -->
    <div v-else class="flex-1 overflow-y-auto">

      <!-- Schema-defined sections -->
      <div
        v-for="section in schema.sections"
        :key="section.id"
        class="border-b border-outline-gray-1"
      >
        <button
          type="button"
          class="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-surface-gray-2 transition-colors"
          @click="toggleSection(section.id)"
        >
          <span class="text-xs font-semibold text-ink-gray-7">{{ section.title }}</span>
          <FeatherIcon
            name="chevron-down"
            class="w-3.5 h-3.5 text-ink-gray-4 transition-transform duration-150"
            :class="openSections.has(section.id) ? '' : '-rotate-90'"
          />
        </button>

        <div v-show="openSections.has(section.id)" class="px-3 pb-3 flex flex-col gap-1">
          <PropRow
            v-for="field in section.fields"
            :key="field.key"
            :label="field.label"
            :hint="field.hint"
          >
            <FieldControl :field="field" :value="value(field.key)" @change="set(field.key, $event)" />
          </PropRow>
        </div>
      </div>

      <!-- Padding -->
      <div class="border-b border-outline-gray-1">
        <button
          type="button"
          class="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-surface-gray-2 transition-colors"
          @click="toggleSection('__padding')"
        >
          <span class="text-xs font-semibold text-ink-gray-7">Padding</span>
          <FeatherIcon
            name="chevron-down"
            class="w-3.5 h-3.5 text-ink-gray-4 transition-transform duration-150"
            :class="openSections.has('__padding') ? '' : '-rotate-90'"
          />
        </button>
        <div v-show="openSections.has('__padding')" class="px-3 pb-3">
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
                :modelValue="block.props.padding_left ?? 32"
                @update:modelValue="set('padding_left', Number($event))"
              />
            </PropRow>
            <PropRow label="Right" compact>
              <TextInput type="number" size="sm" :min="0" :max="200"
                :modelValue="block.props.padding_right ?? 32"
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
          class="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-surface-gray-2 transition-colors"
          @click="toggleSection('__spacing')"
        >
          <span class="text-xs font-semibold text-ink-gray-7">Spacing</span>
          <FeatherIcon
            name="chevron-down"
            class="w-3.5 h-3.5 text-ink-gray-4 transition-transform duration-150"
            :class="openSections.has('__spacing') ? '' : '-rotate-90'"
          />
        </button>
        <div v-show="openSections.has('__spacing')" class="px-3 pb-3">
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
      <div class="px-3 py-3 flex gap-2">
        <Button class="flex-1" size="sm" @click="store.duplicateBlock(block.id)">
          <template #prefix><FeatherIcon name="copy" class="w-3.5 h-3.5" /></template>
          Duplicate
        </Button>
        <Button class="flex-1" size="sm" theme="red" variant="subtle" @click="store.removeBlock(block.id)">
          <template #prefix><FeatherIcon name="trash-2" class="w-3.5 h-3.5" /></template>
          Remove
        </Button>
      </div>

    </div>
  </aside>
</template>

<script setup>
import { computed, reactive, watch, defineComponent, h } from "vue";
import { TextInput, Select, Switch, TabButtons, Button, FeatherIcon, Tooltip, Slider } from "frappe-ui";
import { useEditorStore } from "../stores/editor";
import { BLOCK_SCHEMA } from "../blockSchema";

defineProps({ width: { type: Number, default: 288 } });

const store = useEditorStore();
const block = computed(() => store.selectedBlock);
const schema = computed(() => (block.value ? BLOCK_SCHEMA[block.value.type] : null));

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
  if (block.value) store.updateBlockProps(block.value.id, { [key]: val });
}

function hasBooleanOptions(field) {
  return field.options?.some((o) => typeof o.value === "boolean") ?? false;
}

function parseDimension(val) {
  if (!val || val === "auto") return { num: 0, unit: "px" };
  const m = String(val).match(/^(\d*\.?\d+)(px|%)$/);
  if (m) return { num: parseFloat(m[1]), unit: m[2] };
  const n = parseFloat(val);
  return { num: isNaN(n) ? 0 : n, unit: val.includes("px") ? "px" : "%" };
}

const alignOptions = [
  { value: "left",    icon: "align-left",    label: "Left",    hideLabel: true },
  { value: "center",  icon: "align-center",  label: "Center",  hideLabel: true },
  { value: "right",   icon: "align-right",   label: "Right",   hideLabel: true },
  { value: "justify", icon: "align-justify", label: "Justify", hideLabel: true },
];

// ── Sub-components defined inline ───────────────────────────────────────────

// PropRow: label left, slot content right. compact = label only (no fixed width)
const PropRow = defineComponent({
  props: { label: String, hint: String, compact: Boolean },
  setup(props, { slots }) {
    return () => {
      const labelSpan = h("span", {
        class: props.compact
          ? "text-xs text-ink-gray-5 shrink-0"
          : "w-24 shrink-0 text-xs text-ink-gray-5 truncate",
      }, props.label);

      const labelEl = props.hint
        ? h(Tooltip, { text: props.hint, placement: "left" }, { default: () => labelSpan })
        : labelSpan;

      return h("div", { class: "flex items-center gap-2 py-1" }, [
        labelEl,
        h("div", { class: "flex-1 min-w-0" }, slots.default?.()),
      ]);
    };
  },
});

// FieldControl: renders the right control for a field descriptor
const FieldControl = defineComponent({
  props: { field: Object, value: { default: undefined } },
  emits: ["change"],
  setup(props, { emit }) {
    return () => {
      const f = props.field;
      const v = props.value;

      // Color
      if (f.type === "color") {
        return h("div", { class: "flex items-center gap-1.5" }, [
          h("div", { class: "relative w-6 h-6 rounded flex-shrink-0 cursor-pointer border border-outline-gray-2 overflow-hidden" }, [
            h("input", {
              type: "color",
              value: v || "#ffffff",
              onInput: (e) => emit("change", e.target.value),
              class: "absolute inset-0 w-full h-full opacity-0 cursor-pointer",
            }),
            h("div", {
              class: "w-6 h-6",
              style: { backgroundColor: v || "#ffffff" },
            }),
          ]),
          h(TextInput, {
            class: "flex-1 min-w-0",
            size: "sm",
            type: "text",
            modelValue: v,
            "onUpdate:modelValue": (val) => emit("change", val),
          }),
        ]);
      }

      // Select (boolean → Switch)
      if (f.type === "select") {
        if (hasBooleanOptions(f)) {
          return h(Switch, {
            modelValue: !!v,
            "onUpdate:modelValue": (val) => emit("change", val),
          });
        }
        return h(Select, {
          modelValue: v,
          options: f.options,
          size: "sm",
          "onUpdate:modelValue": (val) => emit("change", val),
        });
      }

      // Alignment
      if (f.type === "align") {
        return h(TabButtons, {
          buttons: alignOptions,
          modelValue: v,
          "onUpdate:modelValue": (val) => emit("change", val),
        });
      }

      // Slider
      if (f.type === "slider") {
        return h("div", { class: "flex items-center gap-2" }, [
          h(Slider, {
            modelValue: [v ?? f.min ?? 0],
            min: f.min ?? 0,
            max: f.max ?? 100,
            step: f.step ?? 1,
            size: "sm",
            "onUpdate:modelValue": (arr) => emit("change", arr[0]),
          }),
          h("span", { class: "text-xs text-ink-gray-5 w-8 text-right flex-shrink-0 tabular-nums" },
            `${v ?? f.min ?? 0}${f.unit ?? ""}`),
        ]);
      }

      // Number
      if (f.type === "number") {
        return h("div", { class: "flex items-center gap-1.5" }, [
          h(TextInput, {
            type: "number",
            min: f.min,
            max: f.max,
            size: "sm",
            modelValue: v,
            "onUpdate:modelValue": (val) => emit("change", Number(val)),
          }),
          f.unit ? h("span", { class: "text-xs text-ink-gray-4 flex-shrink-0" }, f.unit) : null,
        ]);
      }

      // Dimension
      if (f.type === "dimension") {
        const { num, unit } = parseDimension(v);
        return h("div", { class: "flex items-center gap-1" }, [
          h(TextInput, {
            type: "number",
            min: 0,
            size: "sm",
            class: "flex-1 min-w-0",
            modelValue: num,
            "onUpdate:modelValue": (val) => emit("change", val + parseDimension(v).unit),
          }),
          h(TabButtons, {
            buttons: [
              { value: "px", label: "px" },
              { value: "%",  label: "%" },
            ],
            modelValue: unit,
            "onUpdate:modelValue": (u) => emit("change", parseDimension(v).num + u),
          }),
          h("button", {
            type: "button",
            title: "Set to auto",
            class: [
              "text-xs font-medium px-1.5 py-1 rounded border transition-colors flex-shrink-0",
              v === "auto"
                ? "bg-ink-gray-8 text-white border-ink-gray-8"
                : "text-ink-gray-5 border-outline-gray-2 hover:bg-surface-gray-2",
            ],
            onClick: () => emit("change", "auto"),
          }, "auto"),
        ]);
      }

      // Default: text
      return h(TextInput, {
        type: "text",
        placeholder: f.placeholder || "",
        size: "sm",
        modelValue: v,
        "onUpdate:modelValue": (val) => emit("change", val),
      });
    };
  },
});
</script>
