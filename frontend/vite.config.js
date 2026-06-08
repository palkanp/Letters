import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import frappeuiPlugin from "frappe-ui/vite";
import path from "path";

export default defineConfig({
  plugins: [
    frappeuiPlugin({ frappeProxy: false, jinjaBootData: false, buildConfig: false }),
    vue(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  build: {
    outDir: "../letters/public/js",
    emptyOutDir: true,
    rollupOptions: {
      input: "src/main.js",
      output: {
        entryFileNames: "letters-builder.js",
        assetFileNames: "letters-builder.[ext]",
      },
    },
  },
  server: {
    port: 8080,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
