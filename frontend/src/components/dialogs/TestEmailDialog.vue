<template>
  <Dialog
    :model-value="modelValue"
    title="Send Test Email"
    size="sm"
    @update:model-value="(v) => { if (!v) emit('update:modelValue', false) }"
  >
    <template #default>
      <div class="flex flex-col gap-3">
        <p class="text-sm text-ink-gray-6">
          A copy with a <strong>[TEST]</strong> subject prefix will be sent to:
        </p>
        <TextInput
          type="email"
          size="sm"
          placeholder="you@example.com"
          :model-value="recipient"
          autofocus
          @update:model-value="emit('update:recipient', $event)"
          @keydown.enter.prevent="recipient && !sending && emit('send')"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex items-center justify-end gap-2 w-full">
        <Button @click="emit('update:modelValue', false)">Cancel</Button>
        <Button
          variant="solid"
          :loading="sending"
          :disabled="!recipient || sending"
          @click="emit('send')"
        >Send test</Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog, Button, TextInput } from "frappe-ui";

defineProps({
  modelValue: Boolean,
  recipient: { type: String, default: "" },
  sending: Boolean,
});
const emit = defineEmits(["update:modelValue", "update:recipient", "send"]);
</script>
