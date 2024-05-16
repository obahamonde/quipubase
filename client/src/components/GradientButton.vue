<script setup lang="ts">
const props = defineProps<{
  text: string;
}>();
</script>
<template>
  <div>
    <button class="v-gradient">
      {{ props.text }}
      <div class="v-gradient-child"></div>
    </button>
  </div>
</template>
<style scoped>
.v-gradient,
.v-gradient-child {
  @apply text-sm px-4 py-2 text-center align-middle text-white rounded-md cursor-pointer scale;
  background: linear-gradient(
    -45deg,
    theme("colors.orange.400"),
    theme("colors.pink.400"),
    theme("colors.blue.400"),
    theme("colors.teal.400")
  );
  background-size: 600%;
  animation: anime 6s linear infinite;
}

.v-gradient-child {
  @apply absolute mt-[-70px] -z-10 animate-fade-in;
  filter: blur(30px);
  opacity: 0.8;
}

@keyframes anime {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}
</style>
