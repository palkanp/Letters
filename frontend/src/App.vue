<template>
  <FrappeUIProvider>
    <LettersDashboard v-if="!activeLetter" @open-letter="openLetter" />
    <BuilderPage v-else :initial-name="activeLetter" @close="closeLetter" />
  </FrappeUIProvider>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { FrappeUIProvider } from "frappe-ui";
import LettersDashboard from "./pages/LettersDashboard.vue";
import BuilderPage from "./pages/BuilderPage.vue";

const activeLetter = ref(null);

function getRouteParam() {
  if (typeof frappe !== "undefined" && frappe.get_route) {
    const route = frappe.get_route();
    // route is ["letter-builder", "<name>"] or ["letter-builder"]
    if (Array.isArray(route) && route.length >= 2 && route[1]) {
      return route[1];
    }
  }
  const params = new URLSearchParams(window.location.search);
  return params.get("name") || null;
}

function openLetter(name) {
  activeLetter.value = name;
  if (typeof frappe !== "undefined" && frappe.set_route) {
    frappe.set_route("letter-builder", name);
  }
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
