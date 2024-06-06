from asyncio import Queue
from dataclasses import dataclass
from typing import Dict, Generic, TypeVar

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


class SubscriberManager(Generic[T]):
    def __init__(self):
        self.exchanges: Dict[str, Exchange[T]] = {}

    async def add_subscriber(self, namespace: str, subscriber: str) -> Queue[T]:
        if namespace not in self.exchanges:
            self.exchanges[namespace] = Exchange(
                channels={}, event="suscribe", namespace=namespace
            )

        queue = Queue[T]()
        channel = Channel(subscriber=subscriber, publisher=queue)
        self.exchanges[namespace].channels[subscriber] = channel

        return queue

    async def remove_subscriber(self, namespace: str, subscriber: str):
        if namespace in self.exchanges:
            if subscriber in self.exchanges[namespace].channels:
                del self.exchanges[namespace].channels[subscriber]
            if not self.exchanges[namespace].channels:
                del self.exchanges[namespace]

    async def notify_subscribers(self, namespace: str, message: T):
        if namespace in self.exchanges:
            for channel in self.exchanges[namespace].channels.values():
                await channel.publisher.put(message)
