from abc import ABC, abstractmethod
from typing import Any, Type
from pydantic.json_schema import model_json_schema
from typing_extensions import TypedDict, Literal, AsyncGenerator
from functools import lru_cache
from pydantic import BaseModel


class Function(TypedDict):
    name: str
    description: str
    parameters: dict[str, object]


class Tool(BaseModel, ABC):
    @abstractmethod
    async def run(self) -> Any:
        pass

    @classmethod
    @lru_cache
    def definition(cls) -> Function:
        return Function(
            name=cls.__name__,
            description=cls.__doc__ or "",
            parameters=model_json_schema().get("properties", {}),  # type: ignore
        )


class Message(TypedDict):
    role: Literal["assistant", "user", "system"]
    content: str


class Agent(BaseModel, ABC):
    model: str
    messages: list[Message]
    tools: list[Type[Tool]]

    @abstractmethod
    async def run(self) -> Any: ...

    @abstractmethod
    async def chat(self) -> AsyncGenerator[Message, None]: ...
