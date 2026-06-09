<template>
  <BlockWrapper :block="block" :index="index">
    <div :style="{ backgroundColor: block.props.background_color, ...paddingStyle }">
      <div :class="alignClass" class="flex gap-2 flex-wrap">
        <a
          v-for="link in visibleLinks"
          :key="link.key"
          :href="block.props[link.key] || '#'"
          target="_blank"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium no-underline transition-opacity hover:opacity-80 select-none"
          :style="{ backgroundColor: block.props.color + '15', color: block.props.color, border: `1px solid ${block.props.color}30` }"
          @click.prevent="store.selectBlock(block.id)"
        >
          <span>{{ link.icon }}</span>
          <span>{{ link.label }}</span>
        </a>
        <span v-if="visibleLinks.length === 0" class="text-xs text-gray-400 italic">
          Add social URLs in the Inspector →
        </span>
      </div>
    </div>
  </BlockWrapper>
</template>

<script setup>
import { computed } from "vue";
import BlockWrapper from "../BlockWrapper.vue";
import { useEditorStore } from "../../stores/editor";
import { usePadding } from "../../composables/usePadding";

const props = defineProps({ block: Object, index: Number });
const store = useEditorStore();

const blockProps = computed(() => props.block.props);
const paddingStyle = usePadding(blockProps);

const ALL_LINKS = [
  { key: "x_url",         label: "X / Twitter", icon: "𝕏" },
  { key: "linkedin_url",  label: "LinkedIn",     icon: "in" },
  { key: "instagram_url", label: "Instagram",    icon: "◎" },
  { key: "facebook_url",  label: "Facebook",     icon: "f" },
  { key: "youtube_url",   label: "YouTube",      icon: "▶" },
  { key: "github_url",    label: "GitHub",       icon: "⌥" },
  { key: "website_url",   label: "Website",      icon: "🌐" },
];

const visibleLinks = computed(() =>
  ALL_LINKS.filter((l) => props.block.props[l.key])
);

const alignClass = computed(() => {
  const a = props.block.props.align || "center";
  return {
    "justify-start":  a === "left",
    "justify-center": a === "center",
    "justify-end":    a === "right",
  };
});
</script>
