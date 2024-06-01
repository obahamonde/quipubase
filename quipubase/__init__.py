from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .documents import app as documents_app
from .vector import app as vector_app
from .const import SERVERS, SUMMARY, JSON_SCHEMA_DESCRIPTION


def create_app() -> FastAPI:
    app = FastAPI(
        title=SUMMARY,
        description=JSON_SCHEMA_DESCRIPTION,
        servers=SERVERS,
    )
    app.include_router(documents_app)
    app.include_router(vector_app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
