<template>
  <Dialog
    :model-value="true"
    title="Template Library"
    message="Pick a starting point. You can change everything."
    size="3xl"
    @update:model-value="(v) => { if (!v) $emit('close') }"
  >
    <template #default>
      <!-- Grid -->
      <div class="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <button
          v-for="tpl in templates"
          :key="tpl.id"
          type="button"
          class="group text-left rounded-xl border-2 border-gray-100 hover:border-gray-900 transition-all overflow-hidden focus:outline-none focus:border-gray-900"
          @click="apply(tpl)"
        >
          <!-- Visual thumbnail -->
          <div class="bg-gray-50 px-4 pt-4 pb-2 space-y-1.5 min-h-[120px] flex flex-col justify-center">
            <div
              v-for="(row, i) in tpl.preview"
              :key="i"
              class="rounded transition-colors"
              :class="row.class"
              :style="row.style"
            />
          </div>
          <!-- Name + description -->
          <div class="px-4 py-3 border-t border-gray-100">
            <p class="text-sm font-semibold text-gray-800 group-hover:text-gray-900">{{ tpl.name }}</p>
            <p class="text-xs text-gray-400 mt-0.5 leading-snug">{{ tpl.description }}</p>
          </div>
        </button>
      </div>

      <!-- Footer note -->
      <p class="text-xs text-ink-gray-5 mt-5">
        Applying a template will <strong>replace</strong> your current canvas. Your saved campaign is not affected until you save.
      </p>
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog } from "frappe-ui";

const emit = defineEmits(["close", "apply"]);

// ── Template definitions ──────────────────────────────────────────────────────
// Each template has:
//   id, name, description
//   preview: array of thumbnail rows (tailwind classes + inline style)
//   blocks:  array of { type, props? } — passed to editorStore.loadTemplate()

const templates = [
  {
    id: "blank",
    name: "Blank",
    description: "Just a header and footer to start from scratch",
    preview: [
      { class: "h-5 bg-gray-800 rounded", style: "" },
      { class: "h-2 bg-gray-200 rounded w-3/4 mx-auto", style: "" },
      { class: "h-2 bg-gray-200 rounded w-1/2 mx-auto mt-4", style: "" },
      { class: "h-4 bg-gray-300 rounded mt-4", style: "" },
    ],
    blocks: [
      { type: "header" },
      { type: "footer" },
    ],
  },

  {
    id: "newsletter",
    name: "Newsletter",
    description: "Classic newsletter layout with hero, content section, and CTA",
    preview: [
      { class: "h-4 bg-gray-800 rounded", style: "" },
      { class: "h-10 bg-gray-200 rounded mt-1", style: "" },
      { class: "h-2 bg-gray-200 rounded mt-2", style: "" },
      { class: "h-2 bg-gray-200 rounded mt-1 w-4/5", style: "" },
      { class: "h-6 bg-gray-700 rounded-full w-24 mx-auto mt-2", style: "" },
      { class: "h-3 bg-gray-200 rounded mt-2", style: "" },
    ],
    blocks: [
      { type: "header" },
      { type: "hero", props: { heading: "This Month's Updates", subheading: "Here's what's new from our team." } },
      { type: "text", props: { content: "Share the highlights of this month: new features, company news, or a story worth telling." } },
      { type: "button", props: { label: "Read More →", url: "#" } },
      { type: "divider" },
      { type: "footer" },
    ],
  },

  {
    id: "announcement",
    name: "Announcement",
    description: "Bold single-message layout for a product launch, event, or news",
    preview: [
      { class: "h-4 bg-gray-800 rounded", style: "" },
      { class: "h-14 bg-indigo-50 rounded mt-1 border border-indigo-100", style: "" },
      { class: "h-7 bg-indigo-600 rounded-full w-28 mx-auto mt-2", style: "" },
      { class: "h-3 bg-gray-200 rounded mt-2", style: "" },
    ],
    blocks: [
      { type: "header" },
      {
        type: "hero",
        props: {
          heading: "We're launching something big",
          subheading: "Mark your calendar. You won't want to miss this.",
          background_color: "#eef2ff",
          heading_color: "#3730a3",
        },
      },
      { type: "button", props: { label: "Learn More", url: "#" } },
      { type: "text", props: { content: "Questions? Just reply to this email and we'd love to hear from you.", align: "center" } },
      { type: "footer" },
    ],
  },

  {
    id: "product_update",
    name: "Product Update",
    description: "Side-by-side image + text sections, great for feature roundups",
    preview: [
      { class: "h-4 bg-gray-800 rounded", style: "" },
      { class: "h-2 bg-gray-300 rounded mt-2 w-1/2", style: "" },
      { class: "h-8 bg-gray-100 rounded mt-1 border border-gray-200", style: "" },
      { class: "h-8 bg-gray-100 rounded mt-1 border border-gray-200", style: "" },
      { class: "h-8 bg-gray-100 rounded mt-1 border border-gray-200", style: "" },
      { class: "h-3 bg-gray-200 rounded mt-2", style: "" },
    ],
    blocks: [
      { type: "header" },
      { type: "text", props: { content: "What's new this week", font_weight: "700", font_size: "20px" } },
      { type: "image_text", props: { heading: "Feature One", text: "Describe what this feature does and why it matters to your users." } },
      { type: "image_text", props: { heading: "Feature Two", text: "Another improvement your users will love. Keep it short and punchy." } },
      { type: "image_text", props: { heading: "Feature Three", text: "A third update worth celebrating. End on a high note." } },
      { type: "divider" },
      { type: "footer" },
    ],
  },

  {
    id: "welcome",
    name: "Welcome Email",
    description: "Warm onboarding email for new users or subscribers",
    preview: [
      { class: "h-4 bg-gray-800 rounded", style: "" },
      { class: "h-12 bg-emerald-50 rounded mt-1 border border-emerald-100", style: "" },
      { class: "h-2 bg-gray-200 rounded mt-2", style: "" },
      { class: "h-2 bg-gray-200 rounded mt-1 w-3/4", style: "" },
      { class: "h-6 bg-emerald-600 rounded-full w-28 mx-auto mt-2", style: "" },
      { class: "h-3 bg-gray-200 rounded mt-2", style: "" },
    ],
    blocks: [
      { type: "header" },
      {
        type: "hero",
        props: {
          heading: "Welcome aboard! 👋",
          subheading: "We're so glad you're here.",
          background_color: "#ecfdf5",
          heading_color: "#065f46",
        },
      },
      { type: "text", props: { content: "Hi there,\n\nThanks for joining us. Here's everything you need to get started." } },
      { type: "button", props: { label: "Get Started", url: "#" } },
      { type: "text", props: { content: "Have a question? Our team is always here to help.", align: "center", text_color: "#6b7280", font_size: "13px" } },
      { type: "footer" },
    ],
  },

  {
    id: "promo",
    name: "Promotional",
    description: "Sales or discount email with a prominent offer",
    preview: [
      { class: "h-4 bg-gray-800 rounded", style: "" },
      { class: "h-12 bg-orange-50 rounded mt-1 border border-orange-100", style: "" },
      { class: "h-6 bg-orange-500 rounded-full w-32 mx-auto mt-2", style: "" },
      { class: "h-2 bg-gray-200 rounded mt-2 w-2/3 mx-auto", style: "" },
      { class: "h-3 bg-gray-200 rounded mt-2", style: "" },
    ],
    blocks: [
      { type: "header" },
      {
        type: "hero",
        props: {
          heading: "50% Off This Weekend Only",
          subheading: "Use code SAVE50 at checkout. Offer ends Sunday.",
          background_color: "#fff7ed",
          heading_color: "#9a3412",
        },
      },
      { type: "button", props: { label: "Shop Now", url: "#" } },
      { type: "text", props: { content: "Sale ends Sunday at midnight. Terms and conditions apply.", align: "center", text_color: "#9ca3af", font_size: "12px" } },
      { type: "divider" },
      { type: "footer" },
    ],
  },
];

function apply(tpl) {
  emit("apply", tpl.blocks);
}
</script>
