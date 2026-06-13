<template>
  <Dialog
    :model-value="modelValue"
    title="Send Test Email"
    message="Send a copy of this campaign so you can preview it in a real inbox."
    size="sm"
    @update:model-value="(v) => { if (!v) emit('update:modelValue', false) }"
  >
    <template #default>
      <p class="text-xs text-ink-gray-5">
        A copy with a <strong>[TEST]</strong> subject prefix will be sent to your account:
      </p>
      <p class="text-sm font-medium text-ink-gray-8 mt-1">{{ recipient }}</p>
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
import { Dialog, Button } from "frappe-ui";

defineProps({
  modelValue: Boolean,
  recipient: { type: String, default: "" },
  sending: Boolean,
});
const emit = defineEmits(["update:modelValue", "send"]);
</script>
