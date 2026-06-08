import { createApp } from "vue";
import { createPinia } from "pinia";
import { createRouter, createWebHistory } from "vue-router";
import { FrappeUI } from "frappe-ui";
import App from "./App.vue";
import "./style.css";

const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: "/", component: () => import("./pages/BuilderPage.vue") }],
});

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.use(FrappeUI);
app.mount("#letters-builder");
