<template>
  <FrappeUIProvider>
    <LettersDashboard v-if="!activeLetter" :is-dark="isDark" :toggle-dark="toggleDark" @open-letter="openLetter" @new-letter="showNewLetterPicker = true" />
    <BuilderPage v-else :initial-name="activeLetter" :is-dark="isDark" :toggle-dark="toggleDark" @close="closeLetter" />
    <TemplatePicker v-if="showNewLetterPicker" :submit="onNewLetterSubmit" @close="showNewLetterPicker = false" />
  </FrappeUIProvider>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { FrappeUIProvider } from "frappe-ui";
import { useDark, useToggle } from "@vueuse/core";
import LettersDashboard from "./pages/LettersDashboard.vue";
import BuilderPage from "./pages/BuilderPage.vue";
import TemplatePicker from "./components/TemplatePicker.vue";

const isDark = useDark({
  // Scope to our own mount root (main.js), not the default 'html' — this page
  // shares the DOM with the rest of Frappe Desk, and setting data-theme on
  // <html> leaked dark styling into Desk itself once you navigated away.
  selector: "#letter-builder",
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
  // A real pushState (default for set_route): opening a letter is a
  // meaningful navigation the user should be able to step back out of one at
  // a time, same as List → Form elsewhere in Desk.
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

// Runs on initial mount AND whenever Frappe redisplays this already-mounted
// page (main.js wires this to the "letters:page-show" event) — that includes
// browser back/forward, which changes the URL without remounting the app, so
// without this activeLetter would keep showing whatever it last showed.
function syncFromRoute() {
  activeLetter.value = getRouteParam();
}

onMounted(() => {
  syncFromRoute();
  window.addEventListener("letters:page-show", syncFromRoute);
});
onUnmounted(() => window.removeEventListener("letters:page-show", syncFromRoute));
</script>
