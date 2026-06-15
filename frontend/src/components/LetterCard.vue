<template>
  <div
    class="group relative bg-surface-base border border-outline-gray-1 rounded-xl overflow-hidden cursor-pointer
           hover:border-outline-gray-3 hover:shadow-md transition-all duration-150"
    @click="$emit('open', letter.name)"
  >
    <!-- Thumbnail area -->
    <div class="bg-surface-gray-2 h-40 flex items-center justify-center border-b border-outline-gray-1 relative overflow-hidden">
      <div class="flex flex-col items-center gap-2 text-ink-gray-4 select-none">
        <FeatherIcon name="mail" class="w-8 h-8" />
        <span class="text-xs font-medium truncate max-w-[140px] text-center px-2">{{ letter.subject || letter.title }}</span>
      </div>
      <!-- Status badge -->
      <span
        class="absolute top-2.5 right-2.5 text-[10px] font-semibold px-2 py-0.5 rounded-full"
        :class="statusClass"
      >{{ letter.status }}</span>
    </div>

    <!-- Card footer -->
    <div class="px-3.5 py-3">
      <p class="text-sm font-medium text-ink-gray-9 truncate leading-snug">{{ letter.title }}</p>
      <p class="text-xs text-ink-gray-5 mt-0.5">{{ relativeTime }}</p>
    </div>

    <!-- Hover actions -->
    <div
      class="absolute inset-0 bg-black/0 group-hover:bg-black/[0.02] transition-colors pointer-events-none"
    />
  </div>
</template>

<script setup>
import { computed } from "vue";
import { FeatherIcon } from "frappe-ui";

const props = defineProps({
  letter: { type: Object, required: true },
});
defineEmits(["open"]);

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
    if (diff < 60) return "Just now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    if (diff < 86400 * 7) return `${Math.floor(diff / 86400)}d ago`;
    return d.toLocaleDateString();
  } catch {
    return "";
  }
});
</script>
