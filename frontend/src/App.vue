<template>
  <FrappeUIProvider>
    <LettersDashboard v-if="!activeLetter" :is-dark="isDark" :toggle-dark="toggleDark" @open-letter="openLetter" @new-letter="showNewLetterPicker = true" />
    <BuilderPage v-else :initial-name="activeLetter" :is-dark="isDark" :toggle-dark="toggleDark" @close="closeLetter" />
    <TemplatePicker v-if="showNewLetterPicker" :submit="onNewLetterSubmit" @close="showNewLetterPicker = false" />
  </FrappeUIProvider>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from "vue";
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

// frappe-ui's Dropdown/Dialog render via <Teleport to="body">, landing outside
// #letter-builder in the DOM — so Tailwind's dark-mode selector
// ([data-theme="dark"], scoped to #letter-builder above) never matches them,
// and every dropdown/modal stayed stuck in light mode regardless of the
// toggle. Mirror the same attribute onto <body>, the actual teleport target,
// and strip it back off on unmount so it doesn't leak into the rest of Desk
// once you navigate away — the exact leak the #letter-builder scoping above
// was already written to prevent.
watch(isDark, (dark) => {
  document.body.setAttribute("data-theme", dark ? "dark" : "light");
}, { immediate: true });

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
    // frappe.set_route()'s route resolution is async (it awaits parsing the
    // new URL before firing this page's "show" event), racing independently
    // against Vue's own reactivity flush of the activeLetter assignment
    // above. If Frappe's page-show fires first, syncFromRoute() below reads
    // frappe.get_route() before it's caught up — landing back on a stale/
    // empty route and clobbering the activeLetter we just set, which is what
    // made the very first click silently do nothing (mounting the builder
    // with no letter) until a second click let the route catch up. Since we
    // already set activeLetter correctly ourselves, skip the very next
    // page-show resync — it can only be reacting to this same navigation.
    _ignoreNextPageShow = true;
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
    _ignoreNextPageShow = true;
    frappe.set_route("letter-builder");
  }
}

// Runs on initial mount AND whenever Frappe redisplays this already-mounted
// page (main.js wires this to the "letters:page-show" event) — that includes
// browser back/forward, which changes the URL without remounting the app, so
// without this activeLetter would keep showing whatever it last showed.
// See the _ignoreNextPageShow comment in openLetter() for why a page-show
// triggered by our OWN navigation needs to be skipped rather than resynced.
let _ignoreNextPageShow = false;
function syncFromRoute() {
  if (_ignoreNextPageShow) {
    _ignoreNextPageShow = false;
    return;
  }
  activeLetter.value = getRouteParam();
}

onMounted(() => {
  syncFromRoute();
  window.addEventListener("letters:page-show", syncFromRoute);
});
onUnmounted(() => {
  window.removeEventListener("letters:page-show", syncFromRoute);
  document.body.removeAttribute("data-theme");
});
</script>
