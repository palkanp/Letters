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
// Frappe creates `frappe.pages["letter-builder"]` and calls `on_page_load(wrapper)`
// once, when the page is first shown. That is the correct moment to mount Vue —
// the wrapper element is guaranteed to be in the DOM. We must NOT use vue-router
// here: the desk URL is `/app/letter-builder`, which no SPA route would match.
if (typeof window !== "undefined" && window.frappe && window.frappe.pages) {
  const page = (frappe.pages["letter-builder"] =
    frappe.pages["letter-builder"] || {});

  // Desk always shows its own app sidebar unless the page opts out via
  // page.page.hide_sidebar (the flag frappe.ui.make_app_page() normally sets
  // up — we don't use that helper, so without this the sidebar was rendered
  // every time this page showed, reserving a blank strip on the left that
  // just happened to be invisible before because a dark-mode style leak was
  // painting it black too).
  page.page = { hide_sidebar: true };

  page.on_page_load = function (wrapper) {
    // frappe-ui's request/upload layer reads window.csrf_token, but Desk only
    // sets frappe.csrf_token. Without this bridge, POSTs through frappe-ui
    // (e.g. the image FileUploader) are rejected for a missing CSRF token.
    if (window.frappe.csrf_token && !window.csrf_token) {
      window.csrf_token = window.frappe.csrf_token;
    }

    // Reuse the div from letter_builder.html if present, otherwise create one.
    let el = wrapper.querySelector("#letter-builder");
    if (!el) {
      el = document.createElement("div");
      el.id = "letter-builder";
      wrapper.appendChild(el);
    }
    mountApp(el);
  };

  // Frappe reuses this same page instance for every visit — browser back/
  // forward and in-desk navigation both just change the sub-route and fire
  // on_page_show, without remounting the Vue app. Forward that as a DOM event
  // so App.vue can resync activeLetter from the new URL.
  page.on_page_show = function () {
    window.dispatchEvent(new CustomEvent("letters:page-show"));
  };

} else {
  // Standalone dev (vite dev server / index.html)
  mountApp("#letter-builder");
}
