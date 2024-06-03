from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .qconst import DESCRIPTION
from .qdoc import app as documents_app
from .qvector import app as vector_app

def create_app(
    routers: list[APIRouter] = [documents_app, vector_app]
) -> FastAPI:
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
        servers=[{"url": "https://oof2utm5ex8z8e-5000.proxy.runpod.net"}, {"url": "http://quipubase-ih27b7zwaa-tl.a.run.app/"}, {"url": "http://db.indiecloud.com"}, {"url": "http://localhost:5454"}]
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

    @api.get("/", tags=["Landing"])
    def _():
        """
        Landing page for QuipuBase.
        """
        return HTMLResponse(
            """
            <html>
                <head>
                    <title>QuipuBase</title>
                </head>
                <body>
                    <h1>QuipuBase</h1>
                    <p>Welcome to QuipuBase, the AI-driven, schema-flexible document store.</p>
                    <p>For more information, visit the <a href="/docs">documentation</a>.</p>
                </body>
            </html>
            """
        )
    
    @api.get("/api/health", tags=["Health"])
    def _():
        """
        Health check endpoint for QuipuBase.
        """
        return {"code": 200, "message": "QuipuBase is running!"}

    @api.get("/", tags=["Root"])
    def _(request: Request):
        """
        Root endpoint.
        """
        return dict(request.headers)

    return api
