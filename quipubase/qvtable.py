# from functools import cached_property
# from sqlite3 import (Blob, Connection, Cursor, DatabaseError, DataError, Error,
#                      InternalError, Row, adapt, complete_statement, connect,
#                      enable_callback_tracebacks, enable_shared_cache,
#                      register_adapter, register_converter)
# from sqlite3.dbapi2 import Connection as ConnectionType
# from sqlite3.dbapi2 import DateFromTicks
# from typing import (Any, Awaitable, Callable, Coroutine, Dict, Generic, List,
#                     Optional, Tuple, Type, TypeVar, Union)

# from .qdoc import QDocument

# Q = TypeVar("Q", bound=QDocument)


# class QVTable(Generic[Q]):
#     document_type: Type[Q]
#     namespace: str

#     @classmethod
#     def __class_getitem__(cls, item: Type[Q]) -> Type["QVTable[Q]"]:
#         cls.document_type = item
#         return cls

#     @cached_property
#     def table_name(self) -> str:
#         return f"{self.document_type.__name__.lower()}_{self.namespace}"

#     @cached_property
#     def connection(self) -> Connection:
#         return connect(f"{self.namespace}.db")
