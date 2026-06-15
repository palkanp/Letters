<template>
  <FrappeUIProvider>
    <LettersDashboard v-if="!activeLetter" :is-dark="isDark" :toggle-dark="toggleDark" @open-letter="openLetter" @new-letter="createAndOpen" />
    <BuilderPage v-else :initial-name="activeLetter" :is-dark="isDark" :toggle-dark="toggleDark" @close="closeLetter" />
  </FrappeUIProvider>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { FrappeUIProvider } from "frappe-ui";
import { useDark, useToggle } from "@vueuse/core";
import LettersDashboard from "./pages/LettersDashboard.vue";
import BuilderPage from "./pages/BuilderPage.vue";

// Single source of truth for theme — initialises on dashboard load too.
// initialValue "dark" means: if no stored preference and system is not dark,
// still default to dark.
const isDark = useDark({
  attribute: "data-theme",
  valueDark: "dark",
  valueLight: "light",
  initialValue: "dark",
});
const toggleDark = useToggle(isDark);

const activeLetter = ref(null);

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

// Called from dashboard's "New Letter" logo-dropdown shortcut
async function createAndOpen() {
  const res = await frappe.call({ method: "letters.letters.api.save_campaign", args: {} });
  if (res.message?.name) openLetter(res.message.name);
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
