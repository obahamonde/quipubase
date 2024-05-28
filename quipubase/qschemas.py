from __future__ import annotations

import json
from typing import Any, Dict, List, Literal, Optional, Type, Union

from fastapi import HTTPException
from openai import AsyncOpenAI
from pydantic import BaseModel, Field, create_model  # type: ignore
from typing_extensions import TypeAlias, TypedDict, TypeVar

from .qconst import ACTIONS, MAPPING
from .qproxy import QProxy
from .qtools import Tool
from .qutils import handle

T = TypeVar("T", bound=BaseModel)


Property: TypeAlias = Dict[str, object]


class JsonSchema(TypedDict, total=False):
    title: str
    description: str
    type: str
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
    *, namespace: str, schema: JsonSchema, base: Type[T], action: Optional[ACTIONS]
) -> Type[T]:
    """
    Create a class based on the schema, base class, and action.
    """
    name = schema.get("title", "Model")
    properties = schema.get("properties", {})
    attributes: Dict[str, Any] = {}
    if action and action in ("putDoc", "mergeDoc", "findDocs") or not action:
        for key, value in properties.items():
            attributes[key] = (cast_to_type(namespace, value), ...)  # type: ignore
    elif action and action in (
        "getDoc",
        "deleteDoc",
        "scanDocs",
        "countDocs",
        "existsDoc",
        "synthDocs",
    ):
        for key, value in properties.items():
            attributes[key] = (Optional[cast_to_type(namespace, value)], Field(default=None))  # type: ignore
    elif action:
        raise ValueError(f"Invalid action `{action}`")
    return create_model(f"{name}::{hash(namespace)}", __base__=base, **attributes)  # type: ignore


class SynthethicDataGenerator(Tool, QProxy[AsyncOpenAI]):
    """
    This tool will generate a set of synthetic data samples based on the prompt given by the user, generating the proper `json_schema` and `n` samples.
    """

    json_schema: JsonSchema = Field(
        ..., description="The JSON schema of the data to synthetize."
    )
    n: int = Field(..., description="The number of samples to generate.")

    @handle
    async def run(self, **kwargs: Any) -> Any:
        """
        Generate synthetic data based on the given prompt and n of samples.

        Args:
                        prompt (str): The prompt for generating the synthetic data.
                        n (int): The number of samples to generate.

        Returns:
                        list[object]: A list of generated synthetic data samples.

        Raises:
                        None
        """
        PROMPT = f"""
        Generate a set of exactly{min(self.n,100)} unique and diverse json data samples based on the following JSON schema:
            
            ```json
            {json.dumps(self.json_schema, indent=4)}
            ```
            
        # Instructions
        
        * The object generated will be have a key `data` containing the array of generated samples.
        * The whole data structure must be a valid JSON object with no additional content.
        * The JSON object must be syntactically valid with no backticks or other punctuation. JUST JSON.
        * The JSON array must contain an array of objects, each object representing a sample which must adhere to the schema provided.
        """

        response = await self.__load__().chat.completions.create(
            messages=[{"role": "system", "content": PROMPT}],
            model="llama3-8B-8192",
            max_tokens=8192,
            functions=[self.definition()],
        )
        message = response.choices[0].message
        if message.function_call:
            data = json.loads(message.function_call.arguments)
            obj = self.model_validate(data)
            return await obj.run()
        if message.content:
            return sanitize(message.content)
        raise HTTPException(status_code=500, detail="Error generating synthetic data.")

    def __load__(self):
        return AsyncOpenAI()
