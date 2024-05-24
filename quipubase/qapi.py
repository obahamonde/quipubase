import json
import os
from typing import Awaitable, Callable

import httpx
from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from typing_extensions import TypeAlias

from .qconst import SERVERS, SUMMARY
from .qdoc import app as documents_app
from .qllm import app as llm_app
from .qschemas import SynthethicDataGenerator
from .qvector import app as vector_app

Handler: TypeAlias = Callable[[Request], Awaitable[Response]]

api = FastAPI(
    title="QuipuBase",
    description="AI-Driven, Schema-Flexible Document Store",
    summary=SUMMARY,
    version="0.0.1:alpha",
    servers=[SERVERS],
)
api.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ai = AsyncOpenAI()

AUTH0_URL = os.environ["AUTH0_URL"]


def create_app(
    routers: list[APIRouter] = [documents_app, vector_app, llm_app]
) -> FastAPI:
    """
    Create and configure the QuipuBase API.

    Returns:
            FastAPI: The configured FastAPI application.
    """
    for router in routers:
        api.include_router(router, prefix="/api")

    @api.get("/", tags=["Health"])
    @api.get("/api", tags=["Health"])
    @api.get("/api/health", tags=["Health"])
    def _():
        """
        Health check endpoint for QuipuBase.
        """
        return {"code": 200, "message": "QuipuBase is running!"}

    @api.get("/api/synth", tags=["Synthetic Data"])
    async def _(prompt: str):
        """
        Generates synthetic data based on the given prompt.

        Args:
            prompt (str): The prompt for generating the synthetic data.

        Returns:
            Data: An object with a key `data` containing the array of generated synthetic data samples.
        """
        response = await ai.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8B-8192",
            max_tokens=8192,
            functions=[SynthethicDataGenerator.definition()],
        )
        if response.choices[0].message.function_call:
            args = response.choices[0].message.function_call.arguments
            data = json.loads(args)
            return await SynthethicDataGenerator(**data).run()
        return response.choices[0].message.content

    @api.post("/api/auth", tags=["Authentication"])
    async def _(request: Request):
        """
        Authenticates the user with Auth0.

        Args:
            request (Request): The request object containing the bearer token.

        Returns:
            User: The user information according to Auth0 schema definition.
        """
        bearer = request.headers.get("Authorization")
        if not bearer:
            return {"code": 401, "message": "Unauthorized"}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                AUTH0_URL,
                headers={"Authorization": bearer},
            )
            return response.json()

    @api.get("/", tags=["Root"])
    def _(request: Request):
        """
        Root endpoint.
        """
        return dict(request.headers)

    return api
