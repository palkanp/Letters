import { defineConfig } from "cypress";

export default defineConfig({
  e2e: {
    baseUrl: "http://localhost:8000",
    specPattern: "cypress/e2e/**/*.cy.js",
    supportFile: "cypress/support/e2e.js",
    viewportWidth: 1280,
    viewportHeight: 800,
    // Frappe Desk takes a moment to boot; give commands a generous timeout
    defaultCommandTimeout: 10000,
    env: {
      frappe_user: "Administrator",
      frappe_password: "admin",
    },
  },
});
