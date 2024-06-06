from __future__ import annotations

import asyncio
import base64
import os
import types
from functools import cached_property
from typing import Any, ClassVar, Dict, Optional, Type, TypeVar
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Body, Path, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sse_starlette import EventSourceResponse
from typing_extensions import Literal, Self

from .const import DEF_EXAMPLES, EXAMPLES, JSON_SCHEMA_DESCRIPTION
from .pubsub import SubscriberManager
from .quipubase import Quipu  # pylint: disable=E0611
from .schemas import JsonSchema  # pylint: disable=E0611 # type: ignore
from .schemas import create_class

T = TypeVar("T", bound="QuipuDocument")  # type: ignore


class Base(BaseModel):
    """
    Base class for models in the `quipubase` module.
    """

    def __str__(self) -> str:
        return self.model_dump_json()

    def __repr__(self) -> str:
        return self.model_dump_json()


class CosimResult(Base):
    id: str
    score: float
    content: str | list[str] | list[float]


class Status(Base):
    """
    Represents the status of a document.

    Attributes:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    code (int): The status code.
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    message (str): The status message.
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    key (str, optional): The status key. Defaults to None.
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    definition (JsonSchema, optional): The status definition. Defaults to None.
    """

    code: int
    message: str
    key: str = Field(default=None)
    definition: JsonSchema = Field(default=None)


class TypeDef(BaseModel):
    """
    Represents a type definition.

    Attributes:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    data (Optional[Dict[str, Any]]): The data to be stored if the action is `putDoc`, `mergeDoc`, or `findDocs`.
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    definition (JsonSchema): The JSON schema definition.
    """

    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="The data to be stored if the action is `put`, `merge`, or `findDocs`",
        examples=EXAMPLES,
    )
    definition: JsonSchema = Field(
        ...,
        description=JSON_SCHEMA_DESCRIPTION,
        examples=DEF_EXAMPLES,
    )


class QuipuDocument(Base):
    """
    Represents a document in `quipubase`.

    Attributes:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    _db_instances (ClassVar[dict[str, Quipu]]): A dictionary that stores the instances of the Quipu database.
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    key (str): The key of the document.
    """

    _db_instances: ClassVar[dict[str, Quipu]] = {}
    _subclasses: ClassVar[dict[str, Type[QuipuDocument]]] = {}
    _subscriptions: ClassVar[dict[str, SubscriberManager[QuipuDocument]]] = {}
    key: str = Field(default_factory=lambda: str(uuid4()))

    @classmethod
    def __init_subclass__(cls, **kwargs: Any):
        os.makedirs("db", exist_ok=True)
        cls.__name__ = cls.__name__.replace("::", "/")
        os.makedirs(f"db/{cls.__name__}", exist_ok=True)
        super().__init_subclass__(**kwargs)

        if cls.__name__ not in cls._db_instances:
            cls._db_instances[cls.__name__] = Quipu(f"db/{cls.__name__}")
        if cls.__name__ not in cls._subscriptions:
            cls._subscriptions[cls.__name__] = SubscriberManager[cls]()
        cls._db = cls._db_instances[cls.__name__]

    @classmethod
    def definition(cls) -> JsonSchema:
        """
        Returns the JSON schema definition for the document.

        Returns:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        JsonSchema: The JSON schema definition.
        """
        return JsonSchema(
            title=cls.__name__,
            description=cls.__doc__ or "[No description]",
            type="object",
            properties=cls.model_json_schema().get("properties", {}),
        )

    @types.coroutine
    def put_doc(self):
        """
        Puts the document into the database.

        Returns:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        Status: The status of the operation.
        """
        if self._db.exists(key=self.key):
            self._db.merge_doc(self.key, self.model_dump())
        yield
        self._db.put_doc(self.key, self.model_dump())
        return self

    @classmethod
    @types.coroutine
    def get_doc(cls, *, key: str):
        """
        Retrieves a document from the database.

        Args:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        key (str): The key of the document.

        Returns:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        Optional[Self]: The retrieved document, or None if not found.
        """
        data = cls._db.get_doc(key=key)
        yield
        if data:
            return cls(**data)
        return Status(
            code=404,
            message="Document not found",
            key=key,
            definition=cls.definition(),
        )

    @types.coroutine
    def merge_doc(self):
        """
        Merges the document into `quipubase`.

        Returns:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        Status: The status of the operation.
        """
        self._db.merge_doc(key=self.key, value=self.model_dump())
        yield
        return self

    @classmethod
    @types.coroutine
    def delete_doc(cls, *, key: str):
        """
        Deletes a document from `quipubase`.

        Args:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        key (str): The key of the document.

        Returns:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        Status: The status of the operation.
        """
        cls._db.delete_doc(key=key)
        yield
        return Status(
            code=204,
            message="Document deleted",
            key=key,
            definition=cls.definition(),
        )

    @classmethod
    @types.coroutine
    def scan_docs(cls, *, limit: int = 1000, offset: int = 0):
        """
        Scans documents from `quipubase`.

        Args:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        limit (int): The maximum number of documents to scan.
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        offset (int): The offset of the documents to scan.

        Returns:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        List[Self]: The scanned documents.
        """
        yield
        return [
            cls.model_validate(i)  # pylint: disable=E1101
            for i in cls._db.scan_docs(limit, offset)
        ]

    @classmethod
    @types.coroutine
    def find_docs(cls, limit: int = 1000, offset: int = 0, **kwargs: Any):
        """
        Finds documents querying by the given filters.

        Args:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        limit (int): The maximum number of documents to find.
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        offset (int): The offset of the documents to find.
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        **kwargs (Any): Additional keyword arguments for filtering.

        Returns:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        List[Self]: The found documents.
        """
        response = cls._db.find_docs(limit=limit, offset=offset, kwargs=kwargs)
        yield
        return [cls.model_validate(i) for i in response]

    @classmethod
    @types.coroutine
    def count(cls):
        """
        Counts the number of documents in the database.

        Returns:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        int: The number of documents.
        """
        yield
        return cls._db.count()

    @classmethod
    @types.coroutine
    def exists(cls, *, key: str):
        """
        Checks if a document exists on `quipubase`.

        Args:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        key (str): The key of the document.

        Returns:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        bool: True if the document exists, False otherwise.
        """
        yield
        return cls._db.exists(key=key)

    @classmethod
    async def subscribe(cls, namespace: str, subscriber: str, request: Request):
        """
        Subscribes to the changes of the documents in the database.

        Args:
            namespace (str): The namespace of the document.
            subscriber (str): The subscriber name.
            request (Request): The request object.

        Returns:
            AsyncGenerator[str, None]: An async generator of the changes.
        """
        queue = await cls._subscriptions[cls.__name__].add_subscriber(
            namespace=namespace, subscriber=subscriber
        )
        while True:
            try:
                if await request.is_disconnected():
                    break
                message = await queue.get()
                yield message.model_dump_json()
            except asyncio.CancelledError:
                break
            finally:
                await cls._subscriptions[cls.__name__].remove_subscriber(
                    namespace=namespace, subscriber=subscriber
                )


app = APIRouter(tags=["Document Store"], prefix="/document")


@app.post("/{namespace}")
async def document_action(
    namespace: str = Path(description="The namespace of the document"),
    action: Literal["put", "merge", "find", "get", "delete"] = Query(
        ..., description="The action to perform"
    ),
    key: Optional[str] = Query(
        None, description="The unique identifier of the document"
    ),
    limit: Optional[int] = Query(
        None, description="The maximum number of documents to return"
    ),
    offset: Optional[int] = Query(None, description="The number of documents to skip"),
    definition: TypeDef = Body(...),
):
    """
    `put`: Description: Creates a new document in the database.
    `merge`: Description: Updates an existing document in the database.
    `find`: Description: Finds documents in the database which can be filtered by equality comparison of all the fields specified in the `definition`.
    `get`:Description: Retrieves a document from the database.
    `delete`: Description: Deletes a document from the database
    """
    klass = create_class(
        namespace=namespace,
        schema=definition.definition,
        base=QuipuDocument,
        action=action,
    )
    QuipuDocument._subclasses[klass.__name__] = klass
    if action in ("put", "merge"):
        assert (
            definition.data is not None
        ), f"Data must be provided for action `{action}`"
        if action == "put":
            doc = klass(namespace=namespace, **definition.data)  # type: ignore
            await doc.put_doc()
            await SubscriberManager[klass]().notify_subscribers(namespace, doc)
            return doc
        if action == "merge":
            doc = klass(namespace=namespace, **definition.data)  # type: ignore
            await doc.merge_doc()
            await SubscriberManager[klass]().notify_subscribers(namespace, doc)
            return doc
    if action == "find":
        if definition.data is not None:
            return await klass.find_docs(
                limit=limit or 1000, offset=offset or 0, **definition.data
            )
        return await klass.scan_docs(limit=limit or 1000, offset=offset or 0)
    if action in ("get", "delete"):
        assert key is not None, f"Key must be provided for action `{action}`"
        if action == "get":
            return await klass.get_doc(key=key)
        if action == "delete":
            doc = await klass.get_doc(key=key)
            assert isinstance(doc, klass), "Document not found"
            await SubscriberManager[klass]().notify_subscribers(namespace, doc)
            return await klass.delete_doc(key=key)


@app.get("/{namespace}/subscribe")
async def document_subscribe(
    request: Request,
    namespace: str = Path(description="The namespace of the document"),
    subscriber: str = Query(..., description="The subscriber name"),
):
    """
    Subscribes to the changes of the documents in the database.
    """
    klass = QuipuDocument._subclasses[namespace]
    return EventSourceResponse(klass.subscribe(namespace, subscriber, request))
