<script setup lang="ts">
const { speech, isListening, result, fetchVoice } = useSpeech();
const handleSpeech = async () => {
  if (isListening.value) {
    speech.stop();
    const response = await fetch("/api/chat/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text: result.value }),
    });
    const data = await response.text();
    await fetchVoice(data, "api/audio/", "nova");
    result.value = "";
  } else {
    speech.start();
  }
};
</script>
<template>
  <button class="btn-icon col center hover:bg-black cp">
    <Icon
      :icon="isListening ? 'mdi-microphone-off' : 'mdi-microphone'"
      @click="handleSpeech()"
      class="x2 text-primary hover:text-white"
    />
  </button>
</template>
