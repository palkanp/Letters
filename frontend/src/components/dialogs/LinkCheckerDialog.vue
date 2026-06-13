<template>
  <Dialog
    :model-value="modelValue"
    title="Check Links"
    size="md"
    @update:model-value="(v) => { if (!v) emit('update:modelValue', false) }"
  >
    <template #default>
      <!-- Loading state -->
      <div v-if="checking" class="py-8 flex flex-col items-center gap-3">
        <FeatherIcon name="loader" class="w-6 h-6 text-ink-gray-4 animate-spin" />
        <span class="text-sm text-ink-gray-5">Checking all links…</span>
      </div>

      <!-- Empty state -->
      <div v-else-if="!results.length" class="py-8 flex flex-col items-center gap-2">
        <FeatherIcon name="link" class="w-6 h-6 text-ink-gray-3" />
        <p class="text-sm text-ink-gray-5">No links found in this email.</p>
      </div>

      <!-- Results -->
      <div v-else class="flex flex-col gap-1">
        <!-- Summary row -->
        <div class="flex items-center gap-2 pb-2 mb-1 border-b border-outline-gray-1">
          <Badge v-if="results.filter(r => r.status === 'ok').length" theme="green" variant="subtle" size="sm">
            <template #prefix><FeatherIcon name="check" class="w-3 h-3" /></template>
            {{ results.filter(r => r.status === 'ok').length }} working
          </Badge>
          <Badge v-if="results.filter(r => r.status === 'error').length" theme="red" variant="subtle" size="sm">
            <template #prefix><FeatherIcon name="alert-circle" class="w-3 h-3" /></template>
            {{ results.filter(r => r.status === 'error').length }} broken
          </Badge>
          <Badge v-if="results.filter(r => r.status === 'skipped').length" theme="gray" variant="subtle" size="sm">
            {{ results.filter(r => r.status === 'skipped').length }} skipped
          </Badge>
          <Tooltip v-if="results.filter(r => r.status === 'blocked').length" text="Could not verify from this server (DNS or network unreachable). Links likely work fine for recipients.">
            <Badge theme="orange" variant="subtle" size="sm">
              <template #prefix><FeatherIcon name="shield-off" class="w-3 h-3" /></template>
              {{ results.filter(r => r.status === 'blocked').length }} blocked
            </Badge>
          </Tooltip>
          <Button class="ml-auto" size="xs" variant="ghost" icon-left="refresh-cw" :loading="checking" @click="emit('recheck')">Re-check</Button>
        </div>

        <!-- Link rows -->
        <div class="max-h-80 overflow-y-auto flex flex-col gap-1">
          <div
            v-for="r in results"
            :key="r.url"
            class="rounded border px-3 py-2.5"
            :class="{
              'border-outline-gray-1 bg-surface-gray-1': r.status === 'ok' || r.status === 'skipped',
              'border-outline-red-2 bg-surface-red-1': r.status === 'error',
              'border-outline-amber-2 bg-surface-amber-1': r.status === 'blocked',
            }"
          >
            <!-- Top row: url + badge -->
            <div class="flex items-center gap-2 min-w-0">
              <FeatherIcon
                :name="r.status === 'ok' ? 'check-circle' : r.status === 'skipped' ? 'minus' : r.status === 'blocked' ? 'shield-off' : 'alert-circle'"
                class="w-3.5 h-3.5 flex-shrink-0"
                :class="r.status === 'ok' ? 'text-green-500' : r.status === 'skipped' ? 'text-ink-gray-3' : r.status === 'blocked' ? 'text-orange-500' : 'text-red-500'"
              />
              <span class="text-xs font-mono text-ink-gray-7 truncate flex-1 min-w-0">{{ r.url }}</span>
              <Tooltip v-if="r.status === 'blocked'" text="Server blocked automated requests. Link likely works for real recipients.">
                <Badge theme="orange" variant="subtle" size="sm" class="flex-shrink-0">Blocked</Badge>
              </Tooltip>
              <Badge
                v-else-if="r.status !== 'ok'"
                :theme="r.status === 'skipped' ? 'gray' : 'red'"
                variant="subtle"
                size="sm"
                class="flex-shrink-0"
              >{{ r.status === 'skipped' ? 'Non-HTTP' : r.code ? `${r.code}` : 'Unreachable' }}</Badge>
            </div>

            <!-- Inline fix for broken links -->
            <div v-if="r.status === 'error'" class="mt-2 flex items-center gap-1.5">
              <TextInput
                size="sm"
                class="flex-1 min-w-0"
                placeholder="Replace with correct URL…"
                :modelValue="r._fix || ''"
                @update:modelValue="(v) => r._fix = v"
                @keyup.enter="emit('fix', r)"
              />
              <Button size="sm" variant="solid" :disabled="!r._fix" @click="emit('fix', r)">Fix</Button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog, Button, TextInput, FeatherIcon, Tooltip, Badge } from "frappe-ui";

defineProps({
  modelValue: Boolean,
  checking: Boolean,
  results: { type: Array, default: () => [] },
});
const emit = defineEmits(["update:modelValue", "recheck", "fix"]);
</script>
