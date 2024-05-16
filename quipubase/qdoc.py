from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, List, Optional, TypeVar
from uuid import uuid4

import numpy as np
from fastapi import APIRouter, Body, HTTPException, Path, Query, status
from numpy.typing import NDArray
from pydantic import BaseModel, Field
from typing_extensions import Self

from .qconst import DEF_EXAMPLES, EXAMPLES, JSON_SCHEMA_DESCRIPTION, Action
from .qschemas import JsonSchema, create_class
from .quipubase import Quipu  # pylint: disable=E0611
from .qutils import handle

T = TypeVar("T", bound="QDocument")


class _Base(BaseModel):
    def __str__(self) -> str:
        return self.model_dump_json()

    def __repr__(self) -> str:
        return self.model_dump_json()


class Status(_Base):
    code: int
    message: str
    key: str = Field(default=None)
    definition: JsonSchema = Field(default=None)

class TypeDef(BaseModel):
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="The data to be stored if the action is `putDoc` or `mergeDoc`",
        examples=EXAMPLES,
    )
    definition: JsonSchema = Field(
        ...,
        description=JSON_SCHEMA_DESCRIPTION,
        examples=DEF_EXAMPLES,
    )


class QDocument(_Base):
    _db_instances: ClassVar[dict[str, Quipu]] = {}
    key: str = Field(default_factory=lambda: str(uuid4()))

    @classmethod
    def __init_subclass__(cls, **kwargs: Any):
        os.makedirs("db", exist_ok=True)
        os.makedirs(f"db/{cls.__name__}", exist_ok=True)
        super().__init_subclass__(**kwargs)

        if cls.__name__ not in cls._db_instances:
            cls._db_instances[cls.__name__] = Quipu(f"db/{cls.__name__}")
        cls._db = cls._db_instances[cls.__name__]

    @classmethod
    def definition(cls) -> JsonSchema:
        return JsonSchema(
            title=cls.__name__,
            type="object",
            properties=cls.model_json_schema().get("properties", {}),
        )

    @handle
    def put_doc(self) -> Status:
        if self._db.exists(key=self.key):
            self._db.merge_doc(self.key, self.model_dump())
        self._db.put_doc(self.key, self.model_dump())
        return Status(
            code=201,
            message="Document created",
            key=self.key,
            definition=self.definition(),
        )

    @classmethod
    @handle
    def get_doc(cls, *, key: str) -> Optional[Self]:
        data = cls._db.get_doc(key=key)
        if data:
            return cls(**data)
        return None

    @handle
    def merge_doc(self) -> Status:
        self._db.merge_doc(key=self.key, value=self.model_dump())
        return Status(
            code=200,
            message="Document updated",
            key=self.key,
            definition=self.definition(),
        )

    @classmethod
    @handle
    def delete_doc(cls, *, key: str) -> Status:
        cls._db.delete_doc(key=key)
        return Status(
            code=204,
            message="Document deleted",
            key=key,
            definition=cls.definition(),
        )

    @classmethod
    @handle
    def scan_docs(cls, *, limit: int = 1000, offset: int = 0) -> List[Self]:
        return [
            cls.model_validate(i)  # pylint: disable=E1101
            for i in cls._db.scan_docs(limit, offset)
        ]

    @classmethod
    @handle
    def find_docs(cls, limit: int = 1000, offset: int = 0, **kwargs: Any) -> List[Self]:
        return [
            cls.model_validate(i)  # pylint: disable=E1101
            for i in cls._db.find_docs(limit, offset, kwargs)
        ]

    @classmethod
    @handle
    def count(cls) -> int:
        return cls._db.count()

    @classmethod
    @handle
    def exists(cls, *, key: str) -> bool:
        return cls._db.exists(key=key)


class Embedding(QDocument, ABC):
    @abstractmethod
    async def embed(self, *, content: str) -> NDArray[Any]:
        pass

    @abstractmethod
    async def query(
        self,
        *,
        value: NDArray[np.float32],
    ) -> list[Any]:
        pass

    @abstractmethod
    async def upsert(self, *, content: str | list[str]) -> None:
        pass


app = APIRouter(tags=["document"], prefix="/document")


@app.post("/{namespace}")
async def _(
    namespace: str = Path(description="The namespace of the document"),
    action: Action = Query(..., description="The method to be executed"),
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
    Quipubase is a document database, ChatGPT can perform actions over this database to store, retrieve and delete documents provided by the user or generated with the `synth` method.
    """

    klass = create_class(schema=definition.definition, base=QDocument, action=action)
    if action in ("putDoc", "mergeDoc", "findDocs"):
        assert (
            definition.data is not None
        ), f"Data must be provided for action `{action}`"
        if action == "putDoc":
            doc = klass(namespace=namespace, **definition.data)  # type: ignore
            doc.put_doc()
            return doc
        if action == "mergeDoc":
            doc = klass(namespace=namespace, **definition.data)  # type: ignore
            doc.merge_doc()
            return doc
        if action == "findDocs":
            return klass.find_docs(
                limit=limit or 1000,
                offset=offset or 0,
                namespace=namespace,
                **definition.data,
            )
    if action in ("getDoc", "deleteDoc", "scanDocs"):
        assert key is not None, f"Key must be provided for action `{action}`"
        if action == "getDoc":
            return klass.get_doc(key=key)
        if action == "deleteDoc":
            return klass.delete_doc(key=key)
        return klass.scan_docs(limit=limit or 1000, offset=offset or 0)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action `{action}`",
        )
