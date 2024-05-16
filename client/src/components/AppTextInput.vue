<script setup lang="ts">
const content = ref<string>("");
</script>
<template>
<textarea  class="w-full px-4 py-2 rounded-lg mx-2"
    v-model="content" 
@keydown.enter="$emit('send',content)" placeholder="Type your message here..." />

</template>
<style scoped>

</style>