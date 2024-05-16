<script setup lang="ts">
const router = useRouter();
</script>

<template>
  <main class="col center h-screen">
    <RouterView />
    <div>
      <button class="btn-del" @click="router.back()">Go back</button>
    </div>
  </main>
</template>
