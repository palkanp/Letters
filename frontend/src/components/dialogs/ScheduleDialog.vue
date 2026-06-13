<template>
  <Dialog
    :model-value="modelValue"
    title="Schedule Sending"
    message="The campaign will be sent automatically at the chosen time."
    size="sm"
    @update:model-value="(v) => { if (!v) emit('update:modelValue', false) }"
  >
    <template #default>
      <label class="block text-xs font-medium text-ink-gray-7 mb-1.5">Send at</label>
      <div class="flex gap-2">
        <DatePicker
          :model-value="date"
          format="D MMM YYYY"
          placeholder="Pick a date"
          :min="minDate"
          class="flex-1"
          @update:model-value="(v) => emit('update:date', v)"
        />
        <TimePicker
          :model-value="time"
          placeholder="Pick a time"
          class="flex-1"
          @update:model-value="(v) => emit('update:time', v)"
        />
      </div>
      <p v-if="date && time" class="mt-2 text-xs text-ink-gray-5">
        Sending on {{ formatScheduledAt(date + ' ' + time) }}
      </p>
    </template>
    <template #actions>
      <div class="flex items-center justify-end gap-2 w-full">
        <Button @click="emit('update:modelValue', false)">Cancel</Button>
        <Button
          variant="solid"
          :loading="scheduling"
          :disabled="!date || !time || scheduling"
          @click="emit('schedule')"
        >Schedule</Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog, Button, DatePicker, TimePicker } from "frappe-ui";
import { formatScheduledAt } from "../../utils/builderHelpers";

defineProps({
  modelValue: Boolean,
  date: { type: String, default: "" },
  time: { type: String, default: "" },
  minDate: { type: String, default: "" },
  scheduling: Boolean,
});
const emit = defineEmits(["update:modelValue", "update:date", "update:time", "schedule"]);
</script>
