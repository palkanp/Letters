<template>
  <!--
    Zero-height by default so it consumes no visible space between blocks.
    On hover it expands to show a faint line + centred + button.
  -->
  <div
    class="relative flex items-center justify-center overflow-visible select-none
           h-0 hover:h-6 transition-all duration-150 group"
    style="z-index:10"
    @click.stop
  >
    <!-- faint line -->
    <div class="absolute inset-x-0 top-1/2 -translate-y-1/2 h-px bg-gray-200
                opacity-0 group-hover:opacity-100 transition-opacity" />

    <!-- + button -->
    <button
      type="button"
      title="Add block here"
      class="relative z-10 w-6 h-6 rounded-full flex items-center justify-center text-sm font-semibold leading-none
             opacity-0 group-hover:opacity-100 transition-all
             bg-white border border-gray-300 text-gray-400
             hover:bg-gray-900 hover:text-white hover:border-gray-900 hover:scale-110
             shadow-sm"
      aria-label="Add block here"
      @click.stop="$emit('open', afterIndex)"
    ><FeatherIcon name="plus" class="w-3.5 h-3.5" /></button>
  </div>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui";
defineProps({ afterIndex: { type: Number, required: true } });
defineEmits(["open"]);
</script>
