<template>
  <div class="flex items-center gap-2 py-1">
    <div class="shrink-0" :class="compact ? '' : 'w-24'">
      <component :is="hint ? TooltipWrap : 'span'" :text="hint" placement="left">
        <span class="text-xs text-ink-gray-5" :class="compact ? '' : 'block truncate'">{{ label }}</span>
      </component>
    </div>
    <div class="flex-1 min-w-0">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { Tooltip } from "frappe-ui";
import { defineComponent, h } from "vue";

defineProps({
  label:   { type: String },
  hint:    { type: String, default: null },
  compact: { type: Boolean, default: false },
});

// Thin wrapper so the template can conditionally wrap in Tooltip without v-if duplication
const TooltipWrap = defineComponent({
  props: { text: String, placement: String },
  setup(props, { slots }) {
    return () => h(Tooltip, { text: props.text, placement: props.placement }, slots);
  },
});
</script>
