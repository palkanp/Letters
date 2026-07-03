<template>
  <header class="flex-shrink-0 h-12 bg-surface-base border-b border-outline-gray-1 flex items-center px-4 gap-3 relative">

    <!-- Brand + page menu (Frappe Builder-style left dropdown) -->
    <Dropdown :options="menuOptions" placement="bottom-start">
      <template #default="{ open }">
        <Button
          variant="ghost"
          size="sm"
          aria-label="Letter menu"
          class="flex-shrink-0 gap-1 pl-1.5 pr-1 focus-visible:!ring-0"
        >
          <template #prefix>
            <span class="w-6 h-6 rounded-md bg-[var(--ink-gray-9)] text-ink-white flex items-center justify-center text-xs font-bold flex-shrink-0">L</span>
          </template>
          <template #suffix>
            <span :class="`lucide-${open ? 'chevron-up' : 'chevron-down'} size-3.5 text-ink-gray-4`" aria-hidden="true" />
          </template>
        </Button>
      </template>
    </Dropdown>

    <div class="w-px h-4 bg-outline-gray-2 mx-0.5" />

    <!-- Add block / Add container — icon tools -->
    <Tooltip text="Add block">
      <Button variant="ghost" size="sm" icon="lucide-plus" aria-label="Add block" @click.stop="emit('add-block')" />
    </Tooltip>
    <Tooltip text="Add container">
      <Button variant="ghost" size="sm" icon="lucide-square" aria-label="Add container" @click.stop="emit('add-container')" />
    </Tooltip>
    <Tooltip text="Add text">
      <Button variant="ghost" size="sm" icon="lucide-type" aria-label="Add text" @click.stop="emit('insert', 'text')" />
    </Tooltip>
    <Tooltip text="Add image">
      <Button variant="ghost" size="sm" icon="lucide-image" aria-label="Add image" @click.stop="emit('insert', 'image')" />
    </Tooltip>

    <!-- Centered letter title — absolute so it's centered to the page -->
    <div class="absolute inset-x-0 flex items-center justify-center gap-2 pointer-events-none" style="height:48px;">
      <Button
        variant="ghost"
        size="sm"
        class="pointer-events-auto min-w-0 max-w-sm px-2 py-1"
        title="Letter settings"
        @click="emit('open-settings')"
      >
        <span class="truncate text-sm font-medium text-ink-gray-8">
          {{ letterName || "Untitled Letter" }}
        </span>
      </Button>
      <Transition name="fade">
        <span v-if="saving" class="text-xs text-ink-gray-4 flex-shrink-0">Saving…</span>
        <span v-else-if="savedFlash" class="text-xs text-ink-gray-4 flex-shrink-0">Saved</span>
      </Transition>
    </div>

    <!-- Actions -->
    <div class="flex items-center gap-1.5 flex-shrink-0 ml-auto">

      <Tooltip text="Letter settings">
        <Button
          variant="ghost"
          size="sm"
          icon="lucide-settings"
          aria-label="Letter settings"
          @click="emit('open-settings')"
        />
      </Tooltip>

      <div class="w-px h-4 bg-outline-gray-2 mx-0.5" />

      <!-- Sending: inline live-delivery progress bar -->
      <template v-if="letterStatus === 'Sending'">
        <Tooltip :text="`${deliveredCount} of ${sendProgress.total || 0} delivered${sendProgress.failed ? ` · ${sendProgress.failed} failed` : ''}`">
          <div class="flex items-center gap-2 min-w-[180px]">
            <Progress
              :value="sendProgress.total ? Math.round(deliveredCount / sendProgress.total * 100) : 5"
              size="md"
              class="flex-1"
            />
            <span class="text-xs tabular-nums text-ink-gray-5 flex-shrink-0">
              {{ deliveredCount }}/{{ sendProgress.total }}
              <span v-if="sendProgress.failed" class="text-ink-red-4">· {{ sendProgress.failed }} failed</span>
            </span>
          </div>
        </Tooltip>
        <Tooltip v-if="sendStalled" text="No progress for a while — re-queue the recipients that got stuck.">
          <Button
            label="Resume"
            variant="outline"
            theme="orange"
            size="sm"
            icon="lucide-play"
            :loading="resuming"
            @click="emit('resume-send')"
          />
        </Tooltip>
      </template>

      <!-- Sent / Failed / Partial: status badge only -->
      <template v-else-if="letterStatus === 'Sent' || letterStatus === 'Partial' || letterStatus === 'Failed'">
        <Badge
          :theme="letterStatus === 'Sent' ? 'green' : letterStatus === 'Partial' ? 'orange' : 'red'"
          variant="subtle"
          size="md"
          :icon="letterStatus === 'Sent' ? 'lucide-circle-check' : 'lucide-circle-alert'"
        >
          {{ letterStatus === 'Sent' ? 'Sent' : letterStatus === 'Partial' ? 'Partially sent' : 'Failed' }}
        </Badge>
        <Button
          v-if="letterStatus === 'Failed' || letterStatus === 'Partial'"
          label="Resume"
          variant="outline"
          theme="orange"
          size="sm"
          icon="lucide-play"
          :loading="resuming"
          @click="emit('resume-send')"
        />
      </template>

      <!-- Scheduled: status badge with time -->
      <template v-else-if="letterStatus === 'Scheduled'">
        <Badge theme="blue" variant="subtle" size="md" icon="lucide-clock">
          Scheduled{{ scheduledAt ? ` · ${formatScheduledAt(scheduledAt)}` : '' }}
        </Badge>
      </template>

      <!-- Draft: normal preview + send -->
      <template v-else>
        <Dropdown :options="previewOptions" placement="bottom-end">
          <template #default="{ open }">
            <Button variant="ghost" size="sm">
              Preview
              <template #suffix>
                <span :class="`lucide-${open ? 'chevron-up' : 'chevron-down'} size-3`" aria-hidden="true" />
              </template>
            </Button>
          </template>
        </Dropdown>
        <Dropdown :options="sendOptions" placement="bottom-end">
          <template #default="{ open }">
            <Button variant="solid" size="sm" :disabled="!canSend">
              Send
              <template #suffix>
                <span :class="`lucide-${open ? 'chevron-up' : 'chevron-down'} size-3`" aria-hidden="true" />
              </template>
            </Button>
          </template>
        </Dropdown>
      </template>
    </div>
  </header>
</template>

<script setup>
import { computed } from "vue";
import { Button, Dropdown, Tooltip, Progress, Badge } from "frappe-ui";
import { formatScheduledAt } from "../utils/builderHelpers";

const props = defineProps({
  menuOptions: { type: Array, default: () => [] },
  previewOptions: { type: Array, default: () => [] },
  sendOptions: { type: Array, default: () => [] },
  letterStatus: { type: String, default: null },
  sendProgress: { type: Object, default: () => ({ sent: 0, delivered: 0, failed: 0, total: 0 }) },
  sendStalled: Boolean,
  resuming: Boolean,
  saving: Boolean,
  savedFlash: Boolean,
  letterName: { type: String, default: "" },
  scheduledAt: { type: String, default: "" },
  canSend: Boolean,
});
const emit = defineEmits(["add-block", "add-container", "insert", "open-settings", "resume-send"]);

// Live count of emails actually handed to SMTP. Falls back to the accepted
// (queued) count for older progress payloads that predate `delivered`.
const deliveredCount = computed(
  () => props.sendProgress.delivered ?? props.sendProgress.sent ?? 0,
);
</script>
