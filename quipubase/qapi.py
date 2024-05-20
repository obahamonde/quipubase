import json
import os
import httpx
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI

from .qconst import SERVERS, SUMMARY
from .qdoc import app as documents_app
from .qllm import app as llm_app
from .qschemas import SynthethicDataGenerator
from .qvector import app as vector_app

api = FastAPI(
    title="QuipuBase",
    description="AI-Driven, Schema-Flexible Document Store",
    summary=SUMMARY,
    version="0.0.1:alpha",
    # servers=[SERVERS],
)
api.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["http://localhost:3000"],
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

    @api.get("/")
    @api.get("/api")
    @api.get("/api/health")
    def _():
        return {"code": 200, "message": "QuipuBase is running!"}

    @api.get("/api/synth")
    async def _(prompt: str):
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

    @api.post("/api/auth")
    async def _(request: Request):
        bearer = request.headers.get("Authorization")
        if not bearer:
            return {"code": 401, "message": "Unauthorized"}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                AUTH0_URL,
                headers={"Authorization": bearer},
            )
            return response.json()

    return api
