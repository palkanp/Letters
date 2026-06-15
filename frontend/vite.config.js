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
        format: "iife",
        entryFileNames: "letter-builder.js",
        assetFileNames: "letter-builder.[ext]",
        // IIFE bundles everything into one file — no separate chunk imports
        inlineDynamicImports: true,
      },
    },
  },
  optimizeDeps: {
    // frappe-ui ships raw source with `~icons/...` imports that only its vite
    // plugin can resolve — esbuild's dep-scan must not crawl into it.
    exclude: ["frappe-ui"],
    // CJS deps of frappe-ui still need ESM pre-bundling since the exclude
    // above stops vite from discovering them automatically.
    include: ["feather-icons", "showdown", "highlight.js/lib/core", "interactjs"],
  },
  server: {
    port: 8080,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
