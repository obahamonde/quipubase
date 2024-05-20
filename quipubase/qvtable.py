from typing import (
    TypeVar,
    Generic,
    Type,
    Any,
    Union,
    Optional,
    Tuple,
    List,
    Dict,
    Callable,
    Awaitable,
    Coroutine,
)
from functools import cached_property
from sqlite3 import (
    Connection,
    Cursor,
    connect,
    complete_statement,
    adapt,
    Blob,
    Row,
    register_adapter,
    register_converter,
    DatabaseError,
    DataError,
    Error,
    enable_callback_tracebacks,
    enable_shared_cache,
    InternalError,
)
from sqlite3.dbapi2 import Connection as ConnectionType, DateFromTicks
from .qdoc import QDocument

Q = TypeVar("Q", bound=QDocument)


class QVTable(Generic[Q]):
    document_type: Type[Q]
    namespace: str

    @classmethod
    def __class_getitem__(cls, item: Type[Q]) -> Type["QVTable[Q]"]:
        cls.document_type = item
        return cls

    @cached_property
    def table_name(self) -> str:
        return f"{self.document_type.__name__.lower()}_{self.namespace}"

    @cached_property
    def connection(self) -> Connection:
        return connect(f"{self.namespace}.db")
