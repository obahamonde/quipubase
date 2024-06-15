from __future__ import annotations
import asyncio
from typing import TypeVar, Generic
from typing_extensions import Literal
from dataclasses import dataclass, field
from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


@dataclass
class Event(Generic[T]):
    event: Literal["put", "merge", "delete", "upsert"]
    data: T

    def render(self) -> Event[T]:
        return Event[T](event=self.event, data=self.data.model_dump_json())


@dataclass
class Topic(Generic[T]):
    namespace: str
    queue: asyncio.Queue[Event[T]] = field(default_factory=asyncio.Queue)


@dataclass
class Broker(Generic[T]):
    topics: dict[str, Topic[T]] = field(default_factory=dict)

    def __post_init__(self):
        self.topics = {namespace: Topic(namespace) for namespace in self.topics}

    def __getitem__(self, namespace: str) -> Topic[T]:
        return self.topics[namespace]

    def __setitem__(self, namespace: str, topic: Topic[T]):
        self.topics[namespace] = topic

    def __delitem__(self, namespace: str):
        del self.topics[namespace]

    def __iter__(self):
        return iter(self.topics)

    def __len__(self):
        return len(self.topics)

    def __contains__(self, namespace: str):
        return namespace in self.topics

    def __repr__(self):
        return f"{self.__class__.__name__}({self.topics})"

    def __str__(self):
        return f"{self.__class__.__name__}({self.topics})"


class EventBroker(Broker[T]):
    async def put(self, namespace: str, data: T):
        await self[namespace].queue.put(Event(event="put", data=data))

    async def merge(self, namespace: str, data: T):
        await self[namespace].queue.put(Event(event="merge", data=data))

    async def delete(self, namespace: str, data: T):
        await self[namespace].queue.put(Event(event="delete", data=data))

    async def upsert(self, namespace: str, data: T):
        await self[namespace].queue.put(Event(event="upsert", data=data))

    async def listen(self, namespace: str):
        try:
            yield await self[namespace].queue.get()
        except asyncio.CancelledError:
            pass
