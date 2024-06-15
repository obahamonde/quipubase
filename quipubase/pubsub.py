from asyncio import Queue
from dataclasses import dataclass, field
from typing import AsyncGenerator, Dict, Generic, TypeVar

from typing_extensions import Literal

T = TypeVar("T")


@dataclass
class Channel(Generic[T]):
    subscriber: str
    publisher: Queue[T]


@dataclass
class Exchange(Generic[T]):
    channels: Dict[str, Channel[T]]
    event: Literal["put", "merge", "delete", "suscribe"]
    namespace: str


@dataclass
class PubSub(Generic[T]):
    exchanges: Dict[str, Exchange[T]] = field(default_factory=dict)

    async def sub(self, namespace: str, subscriber: str) -> AsyncGenerator[T, None]:
        if namespace not in self.exchanges:
            self.exchanges[namespace] = Exchange(
                channels={}, event="suscribe", namespace=namespace
            )

        queue = Queue[T]()
        channel = Channel(subscriber=subscriber, publisher=queue)
        self.exchanges[namespace].channels[subscriber] = channel
        while True:
            yield await queue.get()

    def remove(self, namespace: str, subscriber: str):
        if namespace in self.exchanges:
            if subscriber in self.exchanges[namespace].channels:
                del self.exchanges[namespace].channels[subscriber]
            if not self.exchanges[namespace].channels:
                del self.exchanges[namespace]

    async def pub(self, namespace: str, message: T):
        if namespace in self.exchanges:
            for channel in self.exchanges[namespace].channels.values():
                await channel.publisher.put(message)
