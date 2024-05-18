from abc import ABC, abstractmethod
from typing import Any
from openai.types.chat.completion_create_params import Function
from pydantic import BaseModel

class Tool(BaseModel, ABC):
    @classmethod
    def definition(cls):
        _schema = cls.model_json_schema()
        return Function(
            name=cls.__name__,
            parameters=_schema,
            description=cls.__doc__ or "[No description available]",
        )

    @abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        raise NotImplementedError
