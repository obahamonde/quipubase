<script setup lang="ts">
const { fetchVoice } = useSpeech();
const props = defineProps<{
  image: string;
  content: string;
  reverse: boolean;
}>();
</script>
<template>
  <div class="message-wrapper mt-12" :class="{ reverse: !props.reverse }">
    <img class="message-pp" :src="props.image" alt="profile-pic" />
    <div class="message-box-wrapper">
      <Icon
        icon="mdi-play"
        class="btn-icon x1 opacity-50 hover:opacity-100"
        @click="
          fetchVoice(props.content, 'api/audio', reverse ? 'nova' : 'onyx')
        "
      />
      <TextBlock :content="props.content" />
    </div>
  </div>
</template>
