<template>
  <div
    class="group relative bg-surface-base border border-outline-gray-1 rounded-xl overflow-hidden cursor-pointer
           hover:border-outline-gray-3 hover:shadow-md transition-all duration-150"
    @click="$emit('open', letter.name)"
  >
    <!-- Thumbnail area -->
    <div class="h-40 border-b border-outline-gray-1 relative overflow-hidden">
      <LetterThumbnail :name="letter.name" icon-class="w-8 h-8" />
      <!-- Status badge -->
      <span
        class="absolute top-2.5 left-2.5 text-[10px] font-semibold px-2 py-0.5 rounded-full z-10"
        :class="statusClass"
      >{{ letter.status }}</span>
    </div>

    <!-- Card footer -->
    <div class="px-3.5 py-3 flex items-start justify-between gap-2">
      <div class="min-w-0">
        <p class="text-sm font-medium text-ink-gray-9 truncate leading-snug">{{ letter.title }}</p>
        <p class="text-xs text-ink-gray-5 mt-0.5">{{ relativeTime }}</p>
      </div>
      <!-- Always-visible menu button -->
      <button
        class="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-md
               text-ink-gray-4 hover:text-ink-gray-7 hover:bg-surface-gray-2 transition-colors mt-0.5"
        @click.stop="$emit('menu', $event)"
      >
        <FeatherIcon name="more-horizontal" class="w-4 h-4" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { FeatherIcon } from "frappe-ui";
import LetterThumbnail from "./LetterThumbnail.vue";

const props = defineProps({
  letter: { type: Object, required: true },
});
defineEmits(["open", "menu"]);

const statusClass = computed(() => {
  const map = {
    Draft:     "bg-surface-gray-3 text-ink-gray-6",
    Scheduled: "bg-surface-amber-1 text-amber-700",
    Sending:   "bg-surface-blue-1 text-blue-700",
    Sent:      "bg-surface-green-1 text-green-700",
    Partial:   "bg-surface-amber-1 text-amber-700",
    Failed:    "bg-surface-red-1 text-red-700",
  };
  return map[props.letter.status] || map.Draft;
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
