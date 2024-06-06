from __future__ import annotations

import json
from typing import Any, Dict, List, Literal, Optional, Type, Union

from pydantic import BaseModel, Field, create_model  # type: ignore
from typing_extensions import TypeAlias, TypedDict, TypeVar

from .const import MAPPING

T = TypeVar("T", bound=BaseModel)


Property: TypeAlias = Dict[str, object]


class JsonSchema(TypedDict, total=False):
    title: str
    description: str
    type: Literal["object"]
    properties: Property


def sanitize(text: str):
    """
    Sanitize the text by removing the leading and trailing whitespaces.
    """
    if text[:2] == "```":
        text = text[7:]
    if text[-3:] == "```":
        text = text[:-3]
    try:
        jsonified = json.loads(text)
        if "data" in jsonified:
            assert isinstance(jsonified["data"], list)
        else:
            raise ValueError("Invalid JSON format")
    except (Exception, ValueError, IndexError) as e:
        raise Exception(f"{e.__class__.__name__}: {e}") from e  # pylint: disable=W0719
    return jsonified["data"]


def parse_anyof_oneof(
    namespace: str, schema: Dict[str, Any]
) -> Union[Type[BaseModel], None]:
    """
    Parse the 'anyOf' or 'oneOf' schema and return the corresponding Union type.
    """
    if "anyOf" in schema:
        return Union[
            tuple[type](cast_to_type(namespace, sub_schema) for sub_schema in schema["anyOf"])  # type: ignore
        ]
    if "oneOf" in schema:
        return Union[
            tuple[type](cast_to_type(namespace, sub_schema) for sub_schema in schema["oneOf"])  # type: ignore
        ]
    return None


def cast_to_type(namespace: str, schema: Dict[str, Any]) -> Any:
    """
    Cast the schema to the corresponding Python type.
    """
    if "enum" in schema:
        enum_values = tuple(schema["enum"])
        if all(isinstance(value, type(enum_values[0])) for value in enum_values):
            return Literal[enum_values]  # type: ignore
    elif schema.get("type") == "object":
        if schema.get("properties"):
            return create_class(namespace=namespace, schema=schema, base=BaseModel, action=None)  # type: ignore
    elif schema.get("type") == "array":
        return List[cast_to_type(namespace, schema.get("items", {}))]
    return MAPPING.get(schema.get("type", "string"), str)


def create_class(
    *,
    namespace: str,
    schema: JsonSchema,
    base: Type[T],
    action: Optional[
        Literal["put", "get", "merge", "delete", "find", "query", "upsert"]
    ],
) -> Type[T]:
    """
    Create a class based on the schema, base class, and action.
    """
    name = schema.get("title", "Model")
    properties = schema.get("properties", {})
    attributes: Dict[str, Any] = {}
    if action and action in ("put", "merge", "find") or not action:
        for key, value in properties.items():
            attributes[key] = (cast_to_type(namespace, value), ...)  # type: ignore
    elif action and action in (
        "get",
        "delete",
        "scan",
    ):
        for key, value in properties.items():
            attributes[key] = (Optional[cast_to_type(namespace, value)], Field(default=None))  # type: ignore
    elif action:
        raise ValueError(f"Invalid action `{action}`")
    return create_model(f"{name}::{hash(namespace)}", __base__=base, **attributes)  # type: ignore
