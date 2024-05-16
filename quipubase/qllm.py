from dotenv import load_dotenv

load_dotenv()

import os
from typing import Literal, TypeAlias, cast

from fastapi import APIRouter, Body, HTTPException, status
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pydantic import BaseModel, Field
from sse_starlette import EventSourceResponse
from typing_extensions import TypedDict

from quipubase.qdoc import QDocument
from quipubase.qproxy import QProxy

Identifier: TypeAlias = Literal["llama3-8B-8192"]
Role: TypeAlias = Literal["system", "assistant", "user"]
MaxContentLength: int = 8192


class Message(TypedDict):
    content: str
    role: Role


class Chat(QDocument):
    instructions: str = Field(default="You are a chatbot assistant.")
    messages: list[Message]


class LanguageModel(BaseModel, QProxy[AsyncOpenAI]):
    namespace: str = Field(..., description="The namespace of the language model.")
    identifier: Identifier = Field(default="llama3-8B-8192")
    instructions: str = Field(default="You are a chatbot assistant.")
    messages: list[Message] = []

    def __load__(self) -> AsyncOpenAI:
        return AsyncOpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"), api_key=os.getenv("OPENAI_API_KEY")
        )

    async def stream(self, *, request: Chat):
        response = await self.__load__().chat.completions.create(
            messages=cast(
                list[ChatCompletionMessageParam],
                [{"role": "system", "content": request.instructions}]
                + request.messages,
            ),
            model=self.identifier,
            max_tokens=8192,
            stream=True,
            stop=["<|eot_id|>"],
        )
        chunks = ""

        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                chunks += content
                yield content
                self.messages.append({"content": content, "role": "assistant"})
                request.messages.append({"content": content, "role": "assistant"})
        request.merge_doc()

    async def chat(self, *, request: Chat):
        response = await self.__load__().chat.completions.create(
            messages=cast(
                list[ChatCompletionMessageParam],
                [{"role": "system", "content": request.instructions}]
                + [r for r in request.messages],
            ),
            model=self.identifier,
            max_tokens=8192,
            stop=["<|eot_id|>"],
        )
        content = response.choices[0].message.content
        assert content, "No content returned from the model."
        self.messages.append({"content": content, "role": "assistant"})
        request.messages.append({"content": content, "role": "assistant"})
        request.merge_doc()
        return content


app = APIRouter(prefix="/chat", tags=["Chat"])


@app.post("/{namespace}", response_class=EventSourceResponse)
async def stream_chat(namespace: str, request: Chat = Body(...)):
    try:
        llm = LanguageModel(namespace=namespace)
        return StreamingResponse(llm.stream(request=request))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
