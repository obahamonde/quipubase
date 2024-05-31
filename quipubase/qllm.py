from dotenv import load_dotenv

load_dotenv()
import json
import os
from typing_extensions import Literal, TypeAlias, cast

from fastapi import APIRouter, Body, HTTPException, status
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pydantic import BaseModel, Field
from typing_extensions import TypedDict, Type
from quipubase.qtools import Tool
from quipubase.qdoc import QDocument
from quipubase.qproxy import QProxy

Identifier: TypeAlias = Literal["llama3-8B-8192"]
Role: TypeAlias = Literal["system", "assistant", "user"]
MaxContentLength: int = 8192


class Message(TypedDict):
    content: str
    role: Role


class Chat(QDocument):
    namespace: str = Field(..., description="The namespace of the chat document.")
    instructions: str = Field(default="You are a chatbot assistant.")
    messages: list[Message] = Field(default_factory=list)


class LanguageModel(BaseModel, QProxy[AsyncOpenAI]):
    namespace: str = Field(..., description="The namespace of the language model.")
    identifier: Identifier = Field(default="llama3-70B-8192")
    instructions: str = Field(default="You are a chatbot assistant.")
    messages: list[Message] = Field(default_factory=list)
    tools: list[Type[Tool]] = Field(default_factory=list)

    def __load__(self) -> AsyncOpenAI:
        return AsyncOpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"), api_key=os.getenv("OPENAI_API_KEY")
        )

    async def stream(self, *, request: Chat):
        messages = [{"role": "system", "content": request.instructions}]
        messages.extend(request.messages)  # type: ignore
        response = await self.__load__().chat.completions.create(
            messages=cast(list[ChatCompletionMessageParam], messages),
            model=self.identifier,
            max_tokens=8192,
            stream=True,
            stop=["<|eot_id|>"],
            functions=[t.definition() for t in Tool.__subclasses__()],
        )
        chunks = ""
        async for chunk in response:
            f_call = chunk.choices[0].delta.function_call
            if f_call and f_call.name and f_call.arguments:
                for t in self.tools:
                    if t.__name__ == f_call.name:
                        yield await t(**json.loads(f_call.arguments)).run()
                        break
            content = chunk.choices[0].delta.content
            if not content:
                continue
            yield content
            chunks += content
            self.messages.append({"content": content, "role": "assistant"})
            request.messages.append({"content": content, "role": "assistant"})
        request.merge_doc()

    async def chat(self, *, request: Chat):
        messages = [{"role": "system", "content": request.instructions}]
        messages.extend(request.messages)  # type: ignore
        response = await self.__load__().chat.completions.create(
            messages=cast(list[ChatCompletionMessageParam], messages),
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


@app.post("/", response_class=StreamingResponse)
async def stream_chat(request: Chat = Body(...)):
    """
    Streams the text as it is generated by the large language model.

    Args:
            request (Chat): The chat request object.

    Returns:
            StreamingResponse: A text stream response from the large language model.

    Raises:
            HTTPException: If an error occurs during the streaming process.
    """
    try:
        llm = LanguageModel(namespace=request.namespace)
        return StreamingResponse(llm.stream(request=request))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
