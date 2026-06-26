<template>
  <FrappeUIProvider>
    <LettersDashboard v-if="!activeLetter" :is-dark="isDark" :toggle-dark="toggleDark" @open-letter="openLetter" @new-letter="showNewLetterPicker = true" />
    <BuilderPage v-else :initial-name="activeLetter" :is-dark="isDark" :toggle-dark="toggleDark" @close="closeLetter" />
    <TemplatePicker v-if="showNewLetterPicker" :submit="onNewLetterSubmit" @close="showNewLetterPicker = false" />
  </FrappeUIProvider>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { FrappeUIProvider } from "frappe-ui";
import { useDark, useToggle } from "@vueuse/core";
import LettersDashboard from "./pages/LettersDashboard.vue";
import BuilderPage from "./pages/BuilderPage.vue";
import TemplatePicker from "./components/TemplatePicker.vue";

const isDark = useDark({
  attribute: "data-theme",
  valueDark: "dark",
  valueLight: "light",
  initialValue: "dark",
});
const toggleDark = useToggle(isDark);

const activeLetter = ref(null);
const showNewLetterPicker = ref(false);

function getRouteParam() {
  if (typeof frappe !== "undefined" && frappe.get_route) {
    const route = frappe.get_route();
    if (Array.isArray(route) && route.length >= 2 && route[1]) return route[1];
  }
  return new URLSearchParams(window.location.search).get("name") || null;
}

function openLetter(name) {
  activeLetter.value = name;
  if (typeof frappe !== "undefined" && frappe.set_route) {
    frappe.set_route("letter-builder", name);
  }
}

async function onNewLetterSubmit(blocks) {
  const res = await frappe.call({
    method: "letters.letters.api.save_letter",
    args: {
      name: null,
      title: "Untitled Letter",
      subject: "",
      preview_text: "",
      email_width: 600,
      canvas_background: "#ffffff",
      blocks: JSON.stringify(blocks),
      recipient_config: null,
    },
  });
  showNewLetterPicker.value = false;
  openLetter(res.message.name);
}

function closeLetter() {
  activeLetter.value = null;
  if (typeof frappe !== "undefined" && frappe.set_route) {
    frappe.set_route("letter-builder");
  }
}

onMounted(() => {
  const name = getRouteParam();
  if (name) activeLetter.value = name;
});
</script>
