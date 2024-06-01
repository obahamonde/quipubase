import asyncio
from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, Field, WithJsonSchema, computed_field

T = TypeVar("T")


class PubSub(BaseModel, Generic[T]):
    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {asyncio.Queue: lambda q: q.qsize()},
    }
    namespace: str = Field(..., description="The namespace of the PubSub")
    queue: Annotated[
        asyncio.Queue[T],
        WithJsonSchema(
            {
                "title": "Queue",
                "description": "A queue of items",
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "The namespace of the PubSub",
                    },
                    "queue": {
                        "type": "integer",
                        "description": "The max size of the queue",
                    },
                    "size": {"type": "integer"},
                    "is_empty": {"type": "boolean"},
                    "is_full": {"type": "boolean"},
                },
            }
        ),
    ] = Field(default_factory=asyncio.Queue)

    @computed_field(return_type=bool)
    @property
    def is_empty(self) -> bool:
        return self.queue.empty()

    @computed_field(return_type=int)
    @property
    def size(self) -> int:
        return self.queue.qsize()

    @computed_field(return_type=bool)
    @property
    def is_full(self) -> bool:
        return self.queue.full()

    async def pub(self, *, item: T):
        while self.is_full:
            await asyncio.sleep(0.1)
        await self.queue.put(item)

    async def sub(self):
        while True:
            while self.is_empty:
                await asyncio.sleep(0.1)
            yield await self.queue.get()
