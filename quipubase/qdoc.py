from __future__ import annotations

import os
from typing import Any, ClassVar, Dict, List, Optional, TypeVar, Union
from uuid import uuid4

from fastapi import APIRouter, Body, Path, Query
from pydantic import BaseModel, Field
from typing_extensions import Self

from .qconst import Actions, DEF_EXAMPLES, EXAMPLES, JSON_SCHEMA_DESCRIPTION
from .qschemas import JsonSchema  # pylint: disable=E0611 # type: ignore
from .qschemas import create_class
from .quipubase import Quipu  # pylint: disable=E0611

T = TypeVar("T", bound='QDocument') # type: ignore


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
        description="The data to be stored if the action is `putDoc`, `mergeDoc`, or `findDocs`",
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

    def put_doc(self):
        """
        Puts the document into the database.

        Returns:
            Status: The status of the operation.
        """
        if self._db.exists(key=self.key):
            self._db.merge_doc(self.key, self.model_dump())
        self._db.put_doc(self.key, self.model_dump())
        return self

    @classmethod
    def get_doc(cls, *, key: str) -> Union[Self, Status]:
        """
        Retrieves a document from the database.

        Args:
            key (str): The key of the document.

        Returns:
            Optional[Self]: The retrieved document, or None if not found.
        """
        data = cls._db.get_doc(key=key)
        if data:
            return cls(**data)
        return Status(
            code=404,
            message="Document not found",
            key=key,
            definition=cls.definition(),
        )

    def merge_doc(self) -> Self:
        """
        Merges the document into `quipubase`.

        Returns:
            Status: The status of the operation.
        """
        self._db.merge_doc(key=self.key, value=self.model_dump())
        return self

    @classmethod
    def delete_doc(cls, *, key: str) -> Status:
        """
        Deletes a document from `quipubase`.

        Args:
            key (str): The key of the document.

        Returns:
            Status: The status of the operation.
        """
        cls._db.delete_doc(key=key)
        return Status(
            code=204,
            message="Document deleted",
            key=key,
            definition=cls.definition(),
        )

    @classmethod
    def scan_docs(cls, *, limit: int = 1000, offset: int = 0) -> List[Self]:
        """
        Scans documents from `quipubase`.

        Args:
            limit (int): The maximum number of documents to scan.
            offset (int): The offset of the documents to scan.

        Returns:
            List[Self]: The scanned documents.
        """
        return [
            cls.model_validate(i)  # pylint: disable=E1101
            for i in cls._db.scan_docs(limit, offset)
        ]

    @classmethod
    def find_docs(cls, limit: int = 1000, offset: int = 0, **kwargs: Any) -> List[Self]:
        """
        Finds documents querying by the given filters.

        Args:
            limit (int): The maximum number of documents to find.
            offset (int): The offset of the documents to find.
            **kwargs (Any): Additional keyword arguments for filtering.

        Returns:
            List[Self]: The found documents.
        """
        response = cls._db.find_docs(
            limit=limit, offset=offset, kwargs=kwargs
        )
        return [cls.model_validate(i) for i in response]

    @classmethod
    def count(cls) -> int:
        """
        Counts the number of documents in the database.

        Returns:
            int: The number of documents.
        """
        return cls._db.count()

    @classmethod
    def exists(cls, *, key: str) -> bool:
        """
        Checks if a document exists on `quipubase`.

        Args:
            key (str): The key of the document.

        Returns:
            bool: True if the document exists, False otherwise.
        """
        return cls._db.exists(key=key)


app = APIRouter(tags=["Document Store"], prefix="/document")


@app.post("/{namespace}")
def _(
    namespace: str = Path(description="The namespace of the document"),
    action: Actions = Query(..., description="The method to be executed"),
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
        namespace=namespace, schema=definition.definition, base=QuipuDocument, action=action
    )
    if action in ("put", "merge"):
        assert (
            definition.data is not None
        ), f"Data must be provided for action `{action}`"
        if action == "put":
            doc = klass(namespace=namespace, **definition.data)  # type: ignore
            return doc.put_doc()
        if action == "merge":
            doc = klass(namespace=namespace, **definition.data)  # type: ignore
            return doc.merge_doc()
    if action == "find":
        if definition.data is not None:
            return klass.find_docs(limit=limit or 1000, offset=offset or 0,**definition.data)
        return klass.scan_docs(limit=limit or 1000, offset=offset or 0)
    if action in ("get", "delete"):
        assert key is not None, f"Key must be provided for action `{action}`"
        if action == "get":
            return klass.get_doc(key=key)
        if action == "delete":
            return klass.delete_doc(key=key)


