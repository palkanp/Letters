<template>
  <!-- FrappeUIProvider mounts the toast viewport so toast.success/error work anywhere -->
  <FrappeUIProvider>
    <BuilderPage />
  </FrappeUIProvider>
</template>

<script setup>
import { FrappeUIProvider } from "frappe-ui";
import BuilderPage from "./pages/BuilderPage.vue";
</script>
