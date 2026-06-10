import { createApp } from "vue";
import { createPinia } from "pinia";
import { FrappeUI } from "frappe-ui";
import App from "./App.vue";
import "frappe-ui/editor-style.css";
import "./style.css";

function mountApp(target) {
  const app = createApp(App);
  app.use(createPinia());
  app.use(FrappeUI);
  app.mount(target);
  return app;
}

// Inside the Frappe Desk this bundle is injected via the `page_js` hook.
// Frappe creates `frappe.pages["letters-builder"]` and calls `on_page_load(wrapper)`
// once, when the page is first shown. That is the correct moment to mount Vue —
// the wrapper element is guaranteed to be in the DOM. We must NOT use vue-router
// here: the desk URL is `/app/letters-builder`, which no SPA route would match.
if (typeof window !== "undefined" && window.frappe && window.frappe.pages) {
  const page = (frappe.pages["letters-builder"] =
    frappe.pages["letters-builder"] || {});

  page.on_page_load = function (wrapper) {
    // Reuse the div from letters_builder.html if present, otherwise create one.
    let el = wrapper.querySelector("#letters-builder");
    if (!el) {
      el = document.createElement("div");
      el.id = "letters-builder";
      wrapper.appendChild(el);
    }
    mountApp(el);
  };
} else {
  // Standalone dev (vite dev server / index.html)
  mountApp("#letters-builder");
}
