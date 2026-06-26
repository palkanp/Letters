<template>
  <div
    class="group relative rounded-xl overflow-hidden cursor-pointer transition-all duration-150 pt-3 px-3 pb-1"
    :class="props.isDark ? 'hover:bg-white/10' : 'hover:bg-surface-gray-2'"
    @click="$emit('open', letter.name)"
  >
    <!-- Thumbnail area -->
    <div class="h-36 relative [clip-path:inset(0_round_0.5rem)]" :class="props.isDark ? '' : 'border border-outline-gray-2 shadow-sm'">
      <LetterThumbnail :name="letter.name" icon-class="w-8 h-8" />
      <!-- Status badge -->
      <Badge
        :theme="statusTheme"
        variant="subtle"
        size="sm"
        :label="letter.status"
        class="absolute top-2.5 left-2.5 z-10"
      />
    </div>

    <!-- Card footer -->
    <div class="px-1 py-2.5 flex items-start justify-between gap-2">
      <div class="min-w-0">
        <p class="text-sm font-medium truncate leading-snug" :class="props.isDark ? 'text-ink-gray-7' : 'text-ink-gray-8'">{{ letter.title }}</p>
        <p class="text-xs mt-0.5" :class="props.isDark ? 'text-ink-gray-5' : 'text-ink-gray-5'">{{ relativeTime }}</p>
      </div>
      <!-- Always-visible menu button -->
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
import { computed } from "vue";
import { Badge, Button } from "frappe-ui";
import LetterThumbnail from "./LetterThumbnail.vue";

const props = defineProps({
  letter: { type: Object, required: true },
  isDark: { type: Boolean, default: false },
});
defineEmits(["open", "menu"]);

const statusTheme = computed(() => {
  const map = {
    Draft:     "gray",
    Scheduled: "orange",
    Sending:   "blue",
    Sent:      "green",
    Partial:   "orange",
    Failed:    "red",
  };
  return map[props.letter.status] || "gray";
});

const relativeTime = computed(() => {
  if (!props.letter.modified) return "";
  try {
    const d = new Date(props.letter.modified.replace(" ", "T"));
    const diff = (Date.now() - d.getTime()) / 1000;
    if (diff < 60)          return "Edited just now";
    if (diff < 3600)        return `Edited ${Math.floor(diff / 60)} mins ago`;
    if (diff < 86400)       return `Edited ${Math.floor(diff / 3600)} hours ago`;
    if (diff < 86400 * 14)  return `Edited ${Math.floor(diff / 86400)} days ago`;
    if (diff < 86400 * 60)  return `Edited ${Math.floor(diff / (86400 * 7))} weeks ago`;
    if (diff < 86400 * 365) return `Edited ${Math.floor(diff / (86400 * 30))} months ago`;
    return `Edited ${Math.floor(diff / (86400 * 365))} years ago`;
  } catch {
    return "";
  }
});
</script>
