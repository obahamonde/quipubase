<script setup lang="ts">
import type { User, Chat } from "../types";
const props = defineProps<{
  user: User;
}>();

const chatData = reactive<Chat>({
  messages: [],
});

const render = (data: string)=>{
  chatData.messages[chatData.messages.length - 1].content += data;
}
const handle = async (data: string) => {
  chatData.messages.push({
    content: data,
    role: "user",
  });
	chatData.messages.push({
		content: "",
		role: "assistant",	
	});
  await useStream<Chat>(`https://6bxwkv84qjspb1-8000.proxy.runpod.net/api/chat/${props.user.sub}`, chatData, render);
};
</script>
<template>
<div>
<div v-for="(message, index) in chatData.messages" :key="index">
<Message :image="message.role == 'user' ? props.user.picture! : './chatbot.svg'"
:content="message.content" :reverse="message.role === 'user'" />
</div>
<AppTextInput @send=handle />
</div>
</template> 