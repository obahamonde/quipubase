<script setup lang="ts">
useTitle("Home");
useFavicon("/favicon.png");
</script>
<template>
  <section class="col center h-screen">
    <Auth>
      <template #default="{ user }">
        <AppUserInput :user="user" />
      </template>
      <template #landing="{ login }">
        <img src="/favicon.svg" class="w-64" />
        <section class="text-2xl font-script font-bold mt-8 text-gray-700">
          <strong class="font-extrabold">QuipuBase:</strong> An ancestral approach for modern AI application
        </section>
        <GradientButton @click="login" class="mt-8" text="Get Started" />
     


   </template>
    </Auth>
  </section>
</template>

<route lang="yaml">
meta:
  layout: home
</route>
