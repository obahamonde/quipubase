from __future__ import annotations

from contextlib import contextmanager
from functools import cached_property
from sqlite3 import (
    Blob,
    Connection,
    Cursor,
    DatabaseError,
    DataError,
    Error,
    InternalError,
    Row,
    adapt,
    complete_statement,
    connect,
    enable_callback_tracebacks,
    enable_shared_cache,
    register_adapter,
    register_converter,
)
from sqlite3.dbapi2 import Connection as ConnectionType
from sqlite3.dbapi2 import DateFromTicks
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from .qdoc import QDocument

Q = TypeVar("Q", bound=QDocument)
T = TypeVar("T")


@contextmanager
def get_db_connection(
    db_path: str,
    timeout: float = 0.500,
):
    """
    Context manager to get a database connection.

    :param db_path: Path to the database file.
    :param isolation_level: Isolation level for the connection.
    :param timeout: Timeout for the connection.
    :return: Database connection.
    """
    connection = connect(db_path, isolation_level="EXCLUSIVE", timeout=timeout)
    try:
        yield connection
    finally:
        connection.close()


class Session(Generic[Q]):
    def __init__(self, model: Type[Q]) -> None:
        self.model = model

    @cached_property
    def db(self):
        return self.model._db
