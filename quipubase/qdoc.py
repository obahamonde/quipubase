from __future__ import annotations
import os
import types
from typing import Any, ClassVar, Dict, Optional, Type, TypeVar
from uuid import uuid4

from fastapi import APIRouter, Body, Path, Query
from pydantic import BaseModel, Field
from typing_extensions import Literal

from .const import DEF_EXAMPLES, EXAMPLES, JSON_SCHEMA_DESCRIPTION
from .quipubase import Quipu  # pylint: disable=E0611
from .schemas import JsonSchema  # pylint: disable=E0611 # type: ignore
from .schemas import create_class

T = TypeVar("T", bound="QuipuDocument")  # type: ignore


class Base(BaseModel):
    def __str__(self) -> str:
        return self.model_dump_json()

    def __repr__(self) -> str:
        return self.model_dump_json()


class CosimResult(Base):
    id: str
    score: float
    content: str | list[str] | list[float]


class Status(BaseModel):
    code: int
    message: str
    key: str = Field(default=None)
    definition: JsonSchema = Field(default=None)


class TypeDef(BaseModel):
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
    _db_instances: ClassVar[dict[str, Quipu]] = {}
    _subclasses: ClassVar[dict[str, Type[QuipuDocument]]] = {}
    key: str = Field(default_factory=lambda: str(uuid4()))

    @classmethod
    def __init_subclass__(cls, **kwargs: Any):
        os.makedirs("db", exist_ok=True)
        cls.__name__ = cls.__name__.replace("::", "/")
        os.makedirs(f"db/{cls.__name__}", exist_ok=True)
        super().__init_subclass__(**kwargs)

        if cls.__name__ not in cls._db_instances:
            cls._db_instances[cls.__name__] = Quipu(f"db/{cls.__name__}")
        cls._db = cls._db_instances[cls.__name__]

    @classmethod
    def definition(cls) -> JsonSchema:
        return JsonSchema(
            title=cls.__name__,
            description=cls.__doc__ or "[No description]",
            type="object",
            properties=cls.model_json_schema().get("properties", {}),
        )

    @types.coroutine
    def put_doc(self):
        if self._db.exists(key=self.key):
            self._db.merge_doc(self.key, self.model_dump())
        yield
        self._db.put_doc(self.key, self.model_dump())
        return self

    @classmethod
    @types.coroutine
    def get_doc(cls, *, key: str):
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
        self._db.merge_doc(key=self.key, value=self.model_dump())
        yield
        return self

    @classmethod
    @types.coroutine
    def delete_doc(cls, *, key: str):
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
        yield
        return [
            cls.model_validate(i)  # pylint: disable=E1101
            for i in cls._db.scan_docs(limit, offset)
        ]

    @classmethod
    @types.coroutine
    def find_docs(cls, limit: int = 1000, offset: int = 0, **kwargs: Any):
        response = cls._db.find_docs(limit=limit, offset=offset, kwargs=kwargs)
        yield
        return [cls.model_validate(i) for i in response]

    @classmethod
    @types.coroutine
    def count(cls):
        yield
        return cls._db.count()

    @classmethod
    @types.coroutine
    def exists(cls, *, key: str):
        yield
        return cls._db.exists(key=key)


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
    `put`: Description: Creates a new document.
    `merge`: Description: Updates an existing document.
    `find`: Description: Finds documents in filtered by certain criteria.
    `get`:Description: Retrieves a document.
    `delete`: Description: Deletes a document.
    """
    klass = create_class(
        namespace=namespace,
        schema=definition.definition,
        base=QuipuDocument,
        action=action,
    )
    QuipuDocument._subclasses[klass.__name__] = klass  # type: ignore
    if action in ("put", "merge"):
        assert (
            definition.data is not None
        ), f"Data must be provided for action `{action}`"
        if action == "put":
            return await klass(namespace=namespace, **definition.data).put_doc()  # type: ignore
        if action == "merge":
            return await klass(namespace=namespace, **definition.data).merge_doc()  # type: ignore
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
            return await klass.delete_doc(key=key)
