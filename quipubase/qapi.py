from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .const import DESCRIPTION, SERVERS
from .qdoc import app as documents_app
from .qvector import app as vector_app


def create_app(routers: list[APIRouter] = [documents_app, vector_app]) -> FastAPI:
    """
    Create and configure the QuipuBase API.

    Returns:
            FastAPI: The configured FastAPI application.
    """
    api = FastAPI(
        title="QuipuBase",
        description=DESCRIPTION,
        summary="AI-Driven, Schema-Flexible Document Vector  Store",
        version="0.0.3",
        servers=SERVERS,
    )
    api.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in routers:
        api.include_router(router, prefix="/api")

    @api.get("/", tags=["Root"])
    def _():
        """
        Landing page for QuipuBase.
        """
        return RedirectResponse(url="/docs")

    @api.get("/api/health", tags=["Health"])
    def _():
        """
        Health check endpoint for QuipuBase.
        """
        return {"code": 200, "message": "QuipuBase is running!"}

    return api
