from abc import ABC, abstractmethod
from typing import Any
import orjson
from openai import AsyncOpenAI
from openai.types.chat.completion_create_params import Function
from pydantic import BaseModel
from .qproxy import QProxy


class Tool(BaseModel, QProxy[AsyncOpenAI], ABC):
    """
    Base class for tools.
    """

    @classmethod
    def definition(cls):
        _schema = cls.model_json_schema()
        return Function(
            name=cls.__name__,
            parameters=_schema.get("properties", {}),
            description=cls.__doc__ or "[No description available]",
        )

    @abstractmethod
    async def run(self) -> Any:
        raise NotImplementedError

    async def __call__(self, *, prompt: str) -> Any:
        res = await self.__load__().chat.completions.create(
            messages=[{"role": "user", "content": prompt}],  # type: ignore
            model="llama3-8B-8192",
            stream=True,
            functions=[self.definition()],
        )
        async for response in res:
            if response.choices[0].delta.function_call:
                f_call = response.choices[0].delta.function_call
                if f_call and f_call.arguments:
                    kwargs = orjson.loads(f_call.arguments)
                    instance = self.__class__(**kwargs)
                    return await instance.run()
