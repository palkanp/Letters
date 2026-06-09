<template>
  <BlockWrapper :block="block" :index="index">
    <div
      :style="{ height: `${block.props.height || 32}px`, backgroundColor: block.props.background_color || 'transparent' }"
      class="w-full"
    />
  </BlockWrapper>
</template>

<script setup>
import BlockWrapper from "../BlockWrapper.vue";
defineProps({ block: Object, index: Number });
</script>
