<template>
  <!-- color -->
  <ColorPicker
    v-if="field.type === 'color'"
    :model-value="value"
    @update:model-value="emit('change', $event)"
  />

  <!-- boolean select → Switch -->
  <Switch
    v-else-if="field.type === 'select' && hasBooleanOptions"
    :model-value="!!value"
    @update:model-value="emit('change', $event)"
  />

  <!-- select -->
  <Select
    v-else-if="field.type === 'select'"
    :model-value="value"
    :options="resolvedOptions"
    size="sm"
    class="w-full"
    @update:model-value="emit('change', $event)"
  />

  <!-- focus point (draggable) -->
  <FocusPointPicker
    v-else-if="field.type === 'focuspoint'"
    :value="value"
    :block-props="blockProps"
    @change="emit('change', $event)"
  />

  <!-- alignment -->
  <TabButtons
    v-else-if="field.type === 'align'"
    class="w-full [&>div]:flex [&>div]:w-full [&_button]:!flex-1"
    :buttons="field.noJustify ? alignOptionsNoJustify : alignOptions"
    :model-value="value"
    @update:model-value="emit('change', $event)"
  />

  <!-- vertical alignment -->
  <TabButtons
    v-else-if="field.type === 'valign'"
    class="w-full [&>div]:flex [&>div]:w-full [&_button]:!flex-1"
    :buttons="valignOptions"
    :model-value="value"
    @update:model-value="emit('change', $event)"
  />

  <!-- direction -->
  <TabButtons
    v-else-if="field.type === 'direction'"
    class="w-full [&>div]:flex [&>div]:w-full [&_button]:!flex-1"
    :buttons="directionOptions"
    :model-value="value"
    @update:model-value="emit('change', $event)"
  />

  <!-- slider -->
  <div v-else-if="field.type === 'slider'" class="flex items-center gap-2">
    <Slider
      :model-value="[value ?? field.min ?? 0]"
      :min="field.min ?? 0"
      :max="field.max ?? 100"
      :step="field.step ?? 1"
      size="sm"
      @update:model-value="emit('change', $event[0])"
    />
    <span class="text-xs text-ink-gray-5 w-8 text-right flex-shrink-0 tabular-nums">
      {{ value ?? field.min ?? 0 }}{{ field.unit ?? "" }}
    </span>
  </div>

  <!-- number — local ref defers unit formatting until blur/Enter to prevent cursor jumps -->
  <div v-else-if="field.type === 'number'" @focusout.stop="commitNumber">
    <TextInput
      type="text"
      size="sm"
      class="w-full"
      :model-value="localNumber"
      @update:model-value="localNumber = $event"
      @keydown.enter.prevent="commitNumber"
    />
  </div>

  <!-- dimension -->
  <TextInput
    v-else-if="field.type === 'dimension'"
    type="text"
    size="sm"
    :placeholder="field.placeholder || 'auto'"
    :model-value="value"
    @update:model-value="emit('change', $event || undefined)"
  />

  <!-- default: text -->
  <TextInput
    v-else
    type="text"
    :placeholder="field.placeholder || ''"
    size="sm"
    :model-value="value"
    @update:model-value="emit('change', $event)"
  />
</template>

<script setup>
import { computed, nextTick, ref, watch } from "vue";
import { TextInput, Select, Switch, TabButtons, Slider, Button } from "frappe-ui";
import ColorPicker from "./ColorPicker.vue";
import FocusPointPicker from "./FocusPointPicker.vue";

const props = defineProps({
  field:      { type: Object, required: true },
  value:      { default: undefined },
  blockProps: { type: Object, default: () => ({}) },
});
const emit = defineEmits(["change"]);

// Local ref for number fields — mirrors the displayed string ("12px") but only
// commits back to the store on blur or Enter, avoiding cursor-jump on every keystroke.
const localNumber = ref("");
watch(
  () => props.value,
  (v) => { localNumber.value = v != null ? `${v}${props.field.unit || ""}` : ""; },
  { immediate: true },
);
function commitNumber() {
  const n = parseInt(localNumber.value) || 0;
  emit("change", n);
  nextTick(() => {
    localNumber.value = props.value != null ? `${props.value}${props.field.unit || ""}` : "";
  });
}

const resolvedOptions = computed(() =>
  typeof props.field.options === "function"
    ? props.field.options(props.blockProps)
    : props.field.options
);

const hasBooleanOptions = computed(() =>
  resolvedOptions.value?.some((o) => typeof o.value === "boolean") ?? false
);

const alignOptions = [
  { value: "left",    icon: "align-left",    label: "Left",    hideLabel: true },
  { value: "center",  icon: "align-center",  label: "Center",  hideLabel: true },
  { value: "right",   icon: "align-right",   label: "Right",   hideLabel: true },
  { value: "justify", icon: "align-justify", label: "Justify", hideLabel: true },
];
const alignOptionsNoJustify = alignOptions.slice(0, 3);
const valignOptions = [
  { value: "flex-start", icon: "chevron-up",   label: "Top",    hideLabel: true },
  { value: "center",     icon: "minus",         label: "Middle", hideLabel: true },
  { value: "flex-end",   icon: "chevron-down",  label: "Bottom", hideLabel: true },
];
const directionOptions = [
  { value: "row",    icon: "arrow-right", label: "Row",    hideLabel: true },
  { value: "column", icon: "arrow-down",  label: "Column", hideLabel: true },
];

</script>
