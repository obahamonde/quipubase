from __future__ import annotations
import os
import json
from typing import Any, ClassVar, Dict, List, Optional, TypeVar, Union, Type
from uuid import uuid4
from datetime import datetime
from fastapi import APIRouter, Body, Path, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing_extensions import Self, Literal

from .const import DEF_EXAMPLES, EXAMPLES, JSON_SCHEMA_DESCRIPTION
from .schemas import JsonSchema  # pylint: disable=E0611 # type: ignore
from .schemas import create_class
from .quipubase import Quipu  # pylint: disable=E0611
from .pubsub import PubSub

T = TypeVar("T", bound="QDocument")


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
    content: str | list[str]


class MetaData(Base):
    """
    Represents the metadata of a document.

    Attributes:
                                    object:str The entity name.
                                    key:str  The key of the document.
                                    namespace: str The namespace of the document.
                                    action: str The action that was executed.
                                    timestamp: float The timestamp of the action.

    """

    object: str
    key: str
    action: Literal["put", "merge", "delete"]
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


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
                                    data (Optional[Dict[str, Any]]): The data to be stored if the action is `put`, `merge`, or `find`.
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


class QDocument(Base):
    """
    Represents a document in `quipubase`.

    Attributes:
                                    _db_instances (ClassVar[dict[str, Quipu]]): A dictionary that stores the instances of the Quipu database.
                                    key (str): The key of the document.
    """
    _queue: Type[PubSub[MetaData]] = PubSub[MetaData]
    _db_instances: ClassVar[dict[str, Quipu]] = {}
    key: str = Field(default_factory=lambda: str(uuid4()))

    @classmethod
    def __init_subclass__(cls, **kwargs: Any) -> None:
        if not os.path.exists(f"db/{cls.__name__}"):
            os.makedirs(f"db/{cls.__name__}", exist_ok=True)
        cls._db = cls._db_instances[cls.__name__] = Quipu(f"db/{cls.__name__}")
        super().__init_subclass__(**kwargs)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        with open(f"db/{cls.__name__}/config.json", "w") as f:
            json.dump(cls.model_json_schema(), f)
        super().__pydantic_init_subclass__(**kwargs)

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

    @property
    def queue(self) -> PubSub[MetaData]:
        return self._queue(namespace=self.__class__.__name__)

    async def put_doc(self) -> Status:
        """
        Puts the document into the database.

        Returns:
            Status: The status of the operation.
        """
        if self._db.exists(key=self.key):
            self._db.merge_doc(self.key, self.model_dump())
        self._db.put_doc(self.key, self.model_dump())
        await self.queue.pub(
            item=MetaData(
                object=self.__class__.__name__,
                key=self.key,
                action="put",
                timestamp=datetime.now().timestamp(),
            )
        )
        return Status(
            code=201,
            message="Document created",
            key=self.key,
            definition=self.definition(),
        )

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

    async def merge_doc(self) -> Status:
        """
        Merges the document into `quipubase`.

        Returns:
                                        Status: The status of the operation.
        """

        self._db.merge_doc(key=self.key, value=self.model_dump())
        await self.queue.pub(
            item=MetaData(
                object=self.__class__.__name__,
                key=self.key,
                action="merge",
                timestamp=datetime.now().timestamp(),
            )
        )
        return Status(
            code=200,
            message="Document updated",
            key=self.key,
            definition=self.definition(),
        )

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

        query = {k: v for k, v in kwargs.items() if v is not None}
        return [
            cls.model_validate(i)  # pylint: disable=E1101
            for i in cls._db.find_docs(limit, offset, query)
        ]

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
async def _(
    namespace: str = Path(description="The namespace of the document"),
    action: Literal["put", "get", "merge", "delete", "find", "query", "upsert"] = Query(
        ..., description="The method to be executed"
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
    Executes a method on a document in the database.

    `put`:
            Description: Creates a new document in the database.
            Request:
                                            - namespace: The namespace of the document.
                                            - action: The method to be executed.
                                            - definition: The json_schema definition of the document.
                                            - data: The data to be stored.
            Response:
                                            - Document object if it was created successfully.

    `merge`:
            Description: Updates an existing document in the database.
            Request:
                                            - namespace: The namespace of the document.
                                            - action: The method to be executed.
                                            - key: The unique identifier of the document
                                            - definition: The json_schema definition of the document.
                                            - data: The data to be stored.
            Response:
                                            - Document object if it was updated successfully.

    `find`:
            Description: Finds documents in the database which can be filtered by equality comparison of all the fields specified in the `definition`.
            Request:
                                            - namespace: The namespace of the document.
                                            - action: The method to be executed.
                                            - definition: The json_schema definition of the document.
                                            - data: The data to be stored.
            Response:
                                            An array of documents filtered by the data provided.

    `get`:
            Description: Retrieves a document from the database.
            Request:
                                            - namespace: The namespace of the document.
                                            - action: The method to be executed.
                                            - key: The unique identifier of the document
            Response:
                                            - The document object if it exists, otherwise None.

    `delete`:
            Description: Deletes a document from the database.
            Request:
                                            - namespace: The namespace of the document.
                                            - action: The method to be executed.
                                            - key: The unique identifier of the document
            Response:
                                            = Status object with code 204 if the document was deleted successfully.

    `scan`:
            Description: Retrieves all documents from the database.
            Request:
                                            - namespace: The namespace of the document.
                                            - action: The method to be executed.
                                            - limit: The maximum number of documents to return
                                            - offset: The number of documents to skip
            Response:
                                            - An array of documents.

    """
    klass = create_class(
        namespace=namespace, schema=definition.definition, base=QDocument, action=action
    )
    if action == "put":
        doc = klass(namespace=namespace, **definition.data)  # type: ignore
        status = await doc.put_doc()
        if status.code == 201 and status.key:

            return doc
        raise ValueError(f"Error creating document: {status}")
    if action == "find":
        if not definition.data:
            return klass.scan_docs(limit=limit or 1000, offset=offset or 0)
        return klass.find_docs(
            limit=limit or 1000, offset=offset or 0, **definition.data
        )
    if not key:
        raise ValueError("Key is required for get, delete, and merge actions")
    if action == "get":
        return klass.get_doc(key=key)
    if action == "delete":
        await klass._queue(namespace=klass.__name__).pub(  # type: ignore
            item=MetaData(
                object=klass.__name__,
                key=key,
                action="delete",
                timestamp=datetime.now().timestamp(),
            )
        )
        return klass.delete_doc(key=key)
    if action == "merge":
        doc = klass(key=key, **definition.data)  # type: ignore
        await doc.merge_doc()
        return doc


@app.get("/{namespace}")
async def _(namespace: str):
    """
    Retrieves a document from the database.

    Args:
        namespace (str): The namespace of the document.
        key (str): The unique identifier of the document.

    Returns:
        Any: The retrieved document.
    """
    queue = PubSub[MetaData](namespace=namespace)

    async def generator():
        async for item in queue.sub():
            yield item.model_dump_json()

    return StreamingResponse(generator(), media_type="application/json")
