import { defineConfig } from "vitest/config";
import vue from "@vitejs/plugin-vue";
import path from "path";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
      // Stub frappe-ui in tests — we only need the pieces we actually import
      "frappe-ui": path.resolve(__dirname, "src/__tests__/__mocks__/frappe-ui.js"),
    },
  },
  test: {
    environment: "happy-dom",
    globals: true,
    include: ["src/__tests__/**/*.test.js"],
  },
});
