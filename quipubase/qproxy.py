from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, Iterable, TypeVar, cast
from dataclasses import dataclass, field
import httpx
from typing_extensions import override

T = TypeVar("T")


class QProxy(Generic[T], ABC):
    """Implements data methods to pretend that an instance is another instance.

    This includes forwarding attribute access and other methods.
    """

    # Note: we have to special case proxies that themselves return proxies
    # to support using a proxy as a catch-all for any random access, e.g. `proxy.foo.bar.baz`

    def __getattr__(self, attr: str) -> object:
        proxied = self.__get_proxied__()
        if isinstance(proxied, QProxy):
            return proxied  # pyright: ignore
        return getattr(proxied, attr)

    @override
    def __repr__(self) -> str:
        proxied = self.__get_proxied__()
        if isinstance(proxied, QProxy):
            return proxied.__class__.__name__
        return repr(self.__get_proxied__())

    @override
    def __str__(self) -> str:
        proxied = self.__get_proxied__()
        if isinstance(proxied, QProxy):
            return proxied.__class__.__name__
        return str(proxied)

    @override
    def __dir__(self) -> Iterable[str]:
        proxied = self.__get_proxied__()
        if isinstance(proxied, QProxy):
            return []
        return proxied.__dir__()

    @property  # type: ignore
    @override
    def __class__(self) -> type:  # pyright: ignore
        proxied = self.__get_proxied__()
        if issubclass(type(proxied), QProxy):
            return type(proxied)
        return proxied.__class__

    def __get_proxied__(self) -> T:
        return self.__load__()

    def __as_proxied__(self) -> T:
        """Helper method that returns the current proxy, typed as the loaded object"""
        return cast(T, self)

    @abstractmethod
    def __load__(self) -> T: ...


@dataclass
class APIClient(QProxy[httpx.AsyncClient]):
    base_url: str = field(repr=False)
    headers: dict[str, str] = field(repr=False)
    timeout: int = field(default=3600, repr=False)

    def __load__(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url, headers=self.headers, timeout=self.timeout
        )

    async def request(
        self,
        *,
        endpoint: str,
        method: str,
        json: dict[str, Any] | None,
        headers: dict[str, str] | None,
    ) -> httpx.Response:
        client = self.__get_proxied__()
        return await client.request(
            method, endpoint, json=json, headers=headers or self.headers
        )

    async def get(
        self,
        *,
        endpoint: str,
        json: dict[str, Any] | None,
        headers: dict[str, str] | None,
    ) -> Any:
        return await self.request(
            endpoint=endpoint, method="GET", json=json, headers=headers
        )

    async def post(
        self,
        *,
        endpoint: str,
        json: dict[str, Any] | None,
        headers: dict[str, str] | None,
    ) -> Any:
        return await self.request(
            endpoint=endpoint, method="POST", json=json, headers=headers
        )

    async def put(
        self,
        *,
        endpoint: str,
        json: dict[str, Any] | None,
        headers: dict[str, str] | None,
    ) -> Any:
        return await self.request(
            endpoint=endpoint, method="PUT", json=json, headers=headers
        )

    async def delete(
        self,
        *,
        endpoint: str,
        json: dict[str, Any] | None,
        headers: dict[str, str] | None,
    ) -> Any:
        return await self.request(
            endpoint=endpoint, method="DELETE", json=json, headers=headers
        )

    async def text(
        self,
        *,
        endpoint: str,
        method: str,
        json: dict[str, Any] | None,
        headers: dict[str, str] | None,
    ) -> str:
        response = await self.request(
            endpoint=endpoint, method=method, json=json, headers=headers
        )
        return response.text

    async def blob(
        self,
        *,
        endpoint: str,
        method: str,
        json: dict[str, Any] | None,
        headers: dict[str, str] | None,
    ) -> bytes:
        response = await self.request(
            endpoint=endpoint, method=method, json=json, headers=headers
        )
        return response.content

    async def stream(
        self,
        *,
        endpoint: str,
        method: str,
        json: dict[str, Any] | None,
        headers: dict[str, str] | None,
    ):
        response = await self.request(
            endpoint=endpoint, method=method, json=json, headers=headers
        )
        async for chunk in response.aiter_bytes():
            yield chunk
