<template>
  <div
    class="group relative rounded-xl overflow-hidden cursor-pointer transition-all duration-150 pt-3 px-3 pb-1"
    :class="props.isDark ? 'hover:bg-white/10' : 'hover:bg-surface-gray-2'"
    @click="$emit('open', notification.letter)"
  >
    <!-- Thumbnail (uses the linked Letter's preview) -->
    <div class="h-36 relative [clip-path:inset(0_round_0.5rem)]" :class="props.isDark ? '' : 'border border-outline-gray-2 shadow-sm'">
      <LetterThumbnail :name="notification.letter" icon-class="w-8 h-8" />
      <Badge
        :theme="notification.enabled ? 'green' : 'gray'"
        variant="subtle"
        size="sm"
        :label="notification.enabled ? 'Enabled' : 'Disabled'"
        class="absolute top-2.5 left-2.5 z-10"
      />
    </div>

    <!-- Footer -->
    <div class="px-1 py-2.5 flex items-start justify-between gap-2">
      <div class="min-w-0">
        <p class="text-sm font-medium truncate leading-snug" :class="props.isDark ? 'text-ink-gray-7' : 'text-ink-gray-8'">{{ notification.name }}</p>
        <p class="text-xs mt-0.5 truncate" :class="props.isDark ? 'text-ink-gray-5' : 'text-ink-gray-5'">
          {{ notification.event }} on {{ notification.document_type }}
        </p>
      </div>
      <Button
        variant="ghost"
        icon="lucide-ellipsis"
        size="sm"
        class="flex-shrink-0 mt-0.5"
        aria-label="More options"
        @click.stop="$emit('menu', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { Badge, Button } from "frappe-ui";
import LetterThumbnail from "./LetterThumbnail.vue";

const props = defineProps({
  notification: { type: Object, required: true },
  isDark: { type: Boolean, default: false },
});
defineEmits(["open", "menu"]);
</script>
