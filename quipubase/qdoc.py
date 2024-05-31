from __future__ import annotations
import json
import os
from typing import Any, ClassVar, Dict, List, Optional, TypeVar, Union
from uuid import uuid4

from fastapi import APIRouter, Body, Path, Query
from pydantic import BaseModel, Field
from typing_extensions import Self

from .qconst import ACTIONS, DEF_EXAMPLES, EXAMPLES, JSON_SCHEMA_DESCRIPTION
from .qschemas import JsonSchema  # pylint: disable=E0611 # type: ignore
from .qschemas import create_class
from .quipubase import Quipu  # pylint: disable=E0611

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


class QDocument(Base):
    """
    Represents a document in `quipubase`.

    Attributes:
                                    _db_instances (ClassVar[dict[str, Quipu]]): A dictionary that stores the instances of the Quipu database.
                                    key (str): The key of the document.
    """

    _db_instances: ClassVar[dict[str, Quipu]] = {}
    key: str = Field(default_factory=lambda: str(uuid4()))

    @classmethod
    def __init_subclass__(cls, **kwargs):
        cls._db: Quipu = Quipu(f"db/{cls.__name__.replace('::', '/')}")
        super().__init_subclass__(**kwargs)

    @classmethod
    def create_table(cls):
        os.makedirs("db", exist_ok=True)
        cls.__name__ = cls.__name__.replace("::", "/")
        if cls.__name__ not in cls._db_instances:
            cls._db_instances[cls.__name__] = Quipu(f"db/{cls.__name__}")
        cls._db = cls._db_instances[cls.__name__]
        with open(f"db/{cls.__name__}/config.json", "w") as f:
            json.dump(cls.definition(), f, indent=4)

    @classmethod
    def drop_table(cls):
        os.remove(f"db/{cls.__name__}/config.json")
        os.remove(f"db/{cls.__name__}")

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

    def put_doc(self) -> Status:
        """
        Puts the document into the database.

        Returns:
                                        Status: The status of the operation.
        """
        if not self.table_exists():
            self.create_table()
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
    def get_doc(cls, *, key: str) -> Union[Self, Status]:
        """
        Retrieves a document from the database.

        Args:
                                        key (str): The key of the document.

        Returns:
                                        Optional[Self]: The retrieved document, or None if not found.
        """

        if not cls.table_exists():
            cls.create_table()
        data = cls._db.get_doc(key=key)
        if data:
            return cls(**data)
        return Status(
            code=404,
            message="Document not found",
            key=key,
            definition=cls.definition(),
        )

    def merge_doc(self) -> Status:
        """
        Merges the document into `quipubase`.

        Returns:
                                        Status: The status of the operation.
        """

        if not self.table_exists():
            self.create_table()
        self._db.merge_doc(key=self.key, value=self.model_dump())
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

        if not cls.table_exists():
            cls.create_table()
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

        if not cls.table_exists():
            cls.create_table()
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

        if not cls.table_exists():
            cls.create_table()
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

        if not cls.table_exists():
            cls.create_table()
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

        if not cls.table_exists():
            cls.create_table()
        return cls._db.exists(key=key)

    @classmethod
    def table_exists(cls) -> bool:
        """
        Checks if the table exists in the database.

        Returns:
                                        bool: True if the table exists, False otherwise.
        """
        return os.path.exists(f"db/{cls.__name__}/config.json")


app = APIRouter(tags=["Document Store"], prefix="/document")


@app.post("/{namespace}")
def _(
    namespace: str = Path(description="The namespace of the document"),
    action: ACTIONS = Query(..., description="The method to be executed"),
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
    `putDoc`:
                                    Description: Creates a new document in the database.
                                    Request:
                                                                    - namespace: The namespace of the document.
                                                                    - action: The method to be executed.
                                                                    - definition: The json_schema definition of the document.
                                                                    - data: The data to be stored.
                                    Response:
                                                                    - Document object if it was created successfully.

    `mergeDoc`:
                                    Description: Updates an existing document in the database.
                                    Request:
                                                                    - namespace: The namespace of the document.
                                                                    - action: The method to be executed.
                                                                    - key: The unique identifier of the document
                                                                    - definition: The json_schema definition of the document.
                                                                    - data: The data to be stored.
                                    Response:
                                                                    - Document object if it was updated successfully.

    `findDocs`:
                                    Description: Finds documents in the database which can be filtered by equality comparison of all the fields specified in the `definition`.
                                    Request:
                                                                    - namespace: The namespace of the document.
                                                                    - action: The method to be executed.
                                                                    - definition: The json_schema definition of the document.
                                                                    - data: The data to be stored.
                                    Response:
                                                                    An array of documents filtered by the data provided.

    `getDoc`:
                                    Description: Retrieves a document from the database.
                                    Request:
                                                                    - namespace: The namespace of the document.
                                                                    - action: The method to be executed.
                                                                    - key: The unique identifier of the document
                                    Response:
                                                                    - The document object if it exists, otherwise None.

    `deleteDoc`:
                                    Description: Deletes a document from the database.
                                    Request:
                                                                    - namespace: The namespace of the document.
                                                                    - action: The method to be executed.
                                                                    - key: The unique identifier of the document
                                    Response:
                                                                    = Status object with code 204 if the document was deleted successfully.

    `scanDocs`:
                                    Description: Retrieves all documents from the database.
                                    Request:
                                                                    - namespace: The namespace of the document.
                                                                    - action: The method to be executed.
                                                                    - limit: The maximum number of documents to return
                                                                    - offset: The number of documents to skip
                                    Response:
                                                                    - An array of documents.
    `createTable`:
                                    Description: Creates a table in the database.
                                    Request:
                                                                    - namespace: The namespace of the document.
                                                                    - action: The method to be executed.
                                    Response:
                                                                    - Status object with code 201 if the table was created successfully.
    `dropTable`:
                                    Description: Drops a table from the database.
                                    Request:
                                                                    - namespace: The namespace of the document.
                                                                    - action: The method to be executed.
                                    Response:
                                                                    - Status object with code 204 if the table was dropped successfully.
    `tableExists`:
                                    Description: Checks if a table exists in the database.
                                    Request:
                                                                    - namespace: The namespace of the document.
                                                                    - action: The method to be executed.
                                    Response:
                                                                    - True if the table exists, False otherwise.
    """
    print(definition.definition["title"])
    klass = create_class(
        namespace=namespace, schema=definition.definition, base=QDocument, action=action
    )
    if action in ("putDoc", "mergeDoc", "findDocs"):
        assert (
            definition.data is not None
        ), f"Data must be provided for action `{action}`"
        if action == "putDoc":
            doc = klass(namespace=namespace, **definition.data)  # type: ignore
            status = doc.put_doc()
            if status.code == 201 and status.key:
                return doc
            raise ValueError(f"Error creating document: {status}")
        if action == "mergeDoc":
            doc = klass(namespace=namespace, **definition.data)  # type: ignore
            doc.merge_doc()
            return doc
        if action == "findDocs":
            print(definition.definition)
            return klass.find_docs(
                limit=limit or 1000,
                offset=offset or 0,
                namespace=namespace,
                **definition.data,
            )
    if action in ("getDoc", "deleteDoc"):
        assert key is not None, f"Key must be provided for action `{action}`"
        if action == "getDoc":
            return klass.get_doc(key=key)
        if action == "deleteDoc":
            return klass.delete_doc(key=key)
    elif action == "scanDocs":
        return klass.scan_docs(limit=limit or 1000, offset=offset or 0)
    elif action == "createTable":
        klass.create_table()
        return Status(
            code=201,
            message="Table created",
            definition=klass.definition(),
        )
    elif action == "dropTable":
        klass.drop_table()
        return Status(
            code=204,
            message="Table dropped",
            definition=klass.definition(),
        )
    raise ValueError(f"Invalid action `{action}`")
