from typing import Literal, TypeAlias

EXAMPLES = [
    {
        "title": "JobPosting",
        "modality": "full-time",
        "location": "Remote",
        "salary": 100000,
        "remote": True,
        "company": {"name": "Acme Inc.", "url": "https://acme.com"},
        "skills": ["python", "fastapi", "aws"],
    }
]

DEF_EXAMPLES = [
    {
        "title": "JobPosting",
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "modality": {
                "type": "string",
                "enum": ["full-time", "part-time", "contract"],
            },
            "location": {"type": "string"},
            "salary": {"type": "number"},
            "remote": {"type": "boolean"},
            "company": {
                "type": "object",
                "title": "Company",
                "properties": {
                    "name": {"type": "string"},
                    "url": {"type": "string"},
                },
            },
            "skills": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["title", "location", "salary", "company"],
    }
]

JSON_SCHEMA_DESCRIPTION = "The `jsonschema` definition of the data, for more information see https://swagger.io/docs/specification/data-models"

MAPPING = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "object": dict,
    "array": list,
    "null": None,
}

SUMMARY = "The `json_schema` standard is well-recognized for defining flexible API schemas, QuipuBase leverages this standard  to provide an intuitive and flexible way to customize the shape of your data, according to your needs with access to a rich set of features such as Retrieval Augmented Generation and Function Calling enabling seamless integrations and agentic workflows on top of essential features such as CRUD operations and search."

Action: TypeAlias = Literal[
    "putDoc",
    "getDoc",
    "mergeDoc",
    "deleteDoc",
    "findDocs",
    "scanDocs",
    "countDocs",
    "existsDoc",
]
