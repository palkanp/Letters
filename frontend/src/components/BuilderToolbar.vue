<template>
  <header class="flex-shrink-0 h-12 bg-white border-b border-outline-gray-1 flex items-center px-4 gap-3 relative">

    <!-- Brand + page menu (Frappe Builder-style left dropdown) -->
    <Dropdown :options="menuOptions" placement="bottom-start">
      <template #default="{ open }">
        <button
          type="button"
          class="flex-shrink-0 flex items-center gap-1 h-8 pl-1.5 pr-1 rounded-md hover:bg-surface-gray-2 transition-colors"
          aria-label="Campaign menu"
        >
          <span class="w-6 h-6 rounded-md bg-gray-900 text-white flex items-center justify-center text-xs font-bold">L</span>
          <FeatherIcon :name="open ? 'chevron-up' : 'chevron-down'" class="w-3.5 h-3.5 text-ink-gray-4" />
        </button>
      </template>
    </Dropdown>

    <div class="w-px h-4 bg-outline-gray-2 mx-0.5" />

    <!-- Add block / Add container — icon tools (Frappe Builder-style) -->
    <Tooltip text="Add block">
      <Button variant="ghost" size="sm" icon="plus" aria-label="Add block" @click.stop="emit('add-block')" />
    </Tooltip>
    <Tooltip text="Add container">
      <Button variant="ghost" size="sm" icon="square" aria-label="Add container" @click.stop="emit('add-container')" />
    </Tooltip>
    <Tooltip text="Add text">
      <Button variant="ghost" size="sm" icon="type" aria-label="Add text" @click.stop="emit('insert', 'text')" />
    </Tooltip>
    <Tooltip text="Add image">
      <Button variant="ghost" size="sm" icon="image" aria-label="Add image" @click.stop="emit('insert', 'image')" />
    </Tooltip>

    <!-- Centered campaign title — absolute so it's centered to the page, not the remaining flex space -->
    <div class="absolute inset-x-0 flex items-center justify-center gap-2 pointer-events-none" style="height:48px;">
      <button
        type="button"
        class="pointer-events-auto flex items-center gap-1.5 min-w-0 max-w-sm px-2 py-1 rounded-md hover:bg-surface-gray-2 transition-colors group"
        title="Campaign settings"
        @click="emit('open-settings')"
      >
        <span class="truncate text-sm font-medium text-ink-gray-8">
          {{ campaignName || "Untitled Campaign" }}
        </span>
      </button>
      <Transition name="fade">
        <span v-if="saving" class="text-xs text-ink-gray-4 flex-shrink-0">Saving…</span>
        <span v-else-if="savedFlash" class="text-xs text-ink-gray-4 flex-shrink-0">Saved</span>
      </Transition>
    </div>

    <!-- Actions -->
    <div class="flex items-center gap-1.5 flex-shrink-0 ml-auto">

      <!-- Settings (gear) — opens the Campaign Settings dialog -->
      <Tooltip text="Campaign settings">
        <Button
          variant="ghost"
          size="sm"
          icon="settings"
          aria-label="Campaign settings"
          @click="emit('open-settings')"
        />
      </Tooltip>

      <div class="w-px h-4 bg-outline-gray-2 mx-0.5" />

      <!-- Sending: inline progress bar -->
      <template v-if="campaignStatus === 'Sending'">
        <div class="flex items-center gap-2 min-w-[180px]">
          <Progress
            :value="sendProgress.total ? Math.round(sendProgress.sent / sendProgress.total * 100) : 5"
            size="md"
            class="flex-1"
          />
          <span class="text-xs tabular-nums text-ink-gray-5 flex-shrink-0">{{ sendProgress.sent }}/{{ sendProgress.total }}</span>
        </div>
      </template>

      <!-- Sent / Failed / Partial: status badge only -->
      <template v-else-if="campaignStatus === 'Sent' || campaignStatus === 'Partial' || campaignStatus === 'Failed'">
        <Badge
          :theme="campaignStatus === 'Sent' ? 'green' : campaignStatus === 'Partial' ? 'orange' : 'red'"
          variant="subtle"
          size="md"
        >
          <template #prefix>
            <FeatherIcon :name="campaignStatus === 'Sent' ? 'check-circle' : 'alert-circle'" class="w-3 h-3" />
          </template>
          {{ campaignStatus === 'Sent' ? 'Sent' : campaignStatus === 'Partial' ? 'Partially sent' : 'Failed' }}
        </Badge>
      </template>

      <!-- Scheduled: status badge with time -->
      <template v-else-if="campaignStatus === 'Scheduled'">
        <Badge theme="blue" variant="subtle" size="md">
          <template #prefix><FeatherIcon name="clock" class="w-3 h-3" /></template>
          Scheduled{{ scheduledAt ? ` · ${formatScheduledAt(scheduledAt)}` : '' }}
        </Badge>
      </template>

      <!-- Draft: normal preview + send -->
      <template v-else>
        <Dropdown :options="previewOptions" placement="bottom-end">
          <template #default="{ open }">
            <Button variant="ghost" size="sm">
              Preview
              <template #suffix><FeatherIcon :name="open ? 'chevron-up' : 'chevron-down'" class="w-3 h-3" /></template>
            </Button>
          </template>
        </Dropdown>
        <Dropdown :options="sendOptions" placement="bottom-end">
          <template #default="{ open }">
            <Button variant="solid" size="sm" :disabled="!canSend">
              Send
              <template #suffix><FeatherIcon :name="open ? 'chevron-up' : 'chevron-down'" class="w-3 h-3" /></template>
            </Button>
          </template>
        </Dropdown>
      </template>
    </div>
  </header>
</template>

<script setup>
import { Button, FeatherIcon, Dropdown, Tooltip, Progress, Badge } from "frappe-ui";
import { formatScheduledAt } from "../utils/builderHelpers";

defineProps({
  menuOptions: { type: Array, default: () => [] },
  previewOptions: { type: Array, default: () => [] },
  sendOptions: { type: Array, default: () => [] },
  campaignStatus: { type: String, default: null },
  sendProgress: { type: Object, default: () => ({ sent: 0, total: 0 }) },
  saving: Boolean,
  savedFlash: Boolean,
  campaignName: { type: String, default: "" },
  scheduledAt: { type: String, default: "" },
  canSend: Boolean,
});
const emit = defineEmits(["add-block", "add-container", "insert", "open-settings"]);
</script>
