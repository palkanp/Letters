<template>
  <Dialog
    :model-value="modelValue"
    title="Keyboard Shortcuts"
    size="sm"
    @update:model-value="(v) => { if (!v) emit('update:modelValue', false) }"
  >
    <template #default>
      <div class="space-y-1 text-sm">
        <div v-for="s in SHORTCUTS" :key="s.label" class="flex items-center justify-between py-1.5 border-b border-outline-gray-1 last:border-0">
          <span class="text-ink-gray-7">{{ s.label }}</span>
          <div class="flex items-center gap-1">
            <kbd v-for="k in s.keys" :key="k" class="inline-flex items-center px-1.5 py-0.5 rounded bg-surface-gray-2 border border-outline-gray-2 text-xs font-mono text-ink-gray-6">{{ k }}</kbd>
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end w-full">
        <Button @click="emit('update:modelValue', false)">Close</Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog, Button } from "frappe-ui";

defineProps({ modelValue: Boolean });
const emit = defineEmits(["update:modelValue"]);

const isMac = navigator.platform.startsWith("Mac") || navigator.userAgent.includes("Mac");
const MOD = isMac ? "⌘" : "Ctrl";
const SHORTCUTS = [
  { label: "Undo",             keys: [MOD, "Z"] },
  { label: "Redo",             keys: [MOD, "⇧", "Z"] },
  { label: "Save",             keys: [MOD, "S"] },
  { label: "Copy block",       keys: [MOD, "C"] },
  { label: "Paste block",      keys: [MOD, "V"] },
  { label: "Duplicate block",  keys: [MOD, "D"] },
  { label: "Delete block",     keys: ["⌫"] },
  { label: "Deselect",         keys: ["Esc"] },
  { label: "Preview",          keys: [MOD, "⇧", "P"] },
  { label: "Zoom in",          keys: [MOD, "+"] },
  { label: "Zoom out",         keys: [MOD, "−"] },
  { label: "Reset zoom",       keys: [MOD, "0"] },
];
</script>
