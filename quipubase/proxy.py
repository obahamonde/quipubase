from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Iterable, Optional, Type, TypeVar, cast

from pydantic import BaseModel, create_model  # type: ignore
from typing_extensions import override

T = TypeVar("T")
T_ = TypeVar("T_", bound=BaseModel)


class Proxy(Generic[T], ABC):
    """Implements data methods to pretend that an instance is another instance.

    This includes forwarding attribute access and other methods.
    """

    # Note: we have to special case proxies that themselves return proxies
    # to support using a proxy as a catch-all for any random access, e.g. `proxy.foo.bar.baz`

    def __getattr__(self, attr: str) -> object:
        proxied = self.__get_proxied__()
        if isinstance(proxied, Proxy):
            return proxied  # pyright: ignore
        return getattr(proxied, attr)

    @override
    def __repr__(self) -> str:
        proxied = self.__get_proxied__()
        if isinstance(proxied, Proxy):
            return proxied.__class__.__name__
        return repr(self.__get_proxied__())

    @override
    def __str__(self) -> str:
        proxied = self.__get_proxied__()
        if isinstance(proxied, Proxy):
            return proxied.__class__.__name__
        return str(proxied)

    @override
    def __dir__(self) -> Iterable[str]:
        proxied = self.__get_proxied__()
        if isinstance(proxied, Proxy):
            return []
        return proxied.__dir__()

    @property  # type: ignore
    @override
    def __class__(self) -> type:  # pyright: ignore
        proxied = self.__get_proxied__()
        if issubclass(type(proxied), Proxy):
            return type(proxied)
        return proxied.__class__

    def __get_proxied__(self) -> T:
        return self.__load__()

    def __as_proxied__(self) -> T:
        """Helper method that returns the current proxy, typed as the loaded object"""
        return cast(T, self)

    @abstractmethod
    def __load__(self) -> T: ...


def create_partial_model(base_model: Type[T]) -> Type[T]:
    """
    Create a new model with all fields optional based on the provided base model.
    """
    fields = {
        name: (Optional[typ], None) for name, typ in base_model.__annotations__.items()
    }
    partial_cls = create_model(f"Partial{base_model.__name__}", **fields)  # type: ignore
    return partial_cls  # type: ignore


class Partial(Generic[T_]):
    """
    Partial class for models, creating a version where all fields are optional.
    """

    @classmethod
    def __class_getitem__(cls, item: Type[T_]) -> Type[T_]:
        return create_partial_model(item)
