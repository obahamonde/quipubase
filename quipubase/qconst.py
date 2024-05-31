from typing_extensions import Literal, TypeAlias

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

SUMMARY = "The json_schema standard is well-recognized for defining flexible API schemas. QuipuBase leverages this standard to offer an intuitive and adaptable way to customize your data structure according to your needs. It provides a rich set of features such as Retrieval Augmented Generation (RAG) and Function Calling, enabling seamless integrations and autonomous workflows, alongside essential functionalities like CRUD operations and search."

SERVERS = {
    "url": "https://db.indiecloud.co",
    "description": "IndieCloud - Quipubase JSON API Server",
}

ACTIONS: TypeAlias = Literal[
    "putDoc", "getDoc", "mergeDoc", "deleteDoc", "findDocs", "scanDocs","createTable","dropTable", "tableExists"
]

IMAGES_URL = "https://api.runpod.ai/v2/s6a87rd752k96z"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer " + "WJCB6JDNWLT9QM8N2FDQ2JQYB7658CIWVJBIRBIU",
}
TIMEOUT = 3600
