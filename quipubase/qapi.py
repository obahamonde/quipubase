import json

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI

from .qconst import SUMMARY
from .qdoc import app as documents_app
from .qschemas import DataSamplingTool
from .qtools import app as tools_app
from .qvector import app as vector_app

api = FastAPI(
    title="QuipuBase",
    description="AI-Driven, Schema-Flexible Document Store",
    summary=SUMMARY,
    version="0.0.1:alpha",
    servers=[{"url": "https://6bxwkv84qjspb1-5000.proxy.runpod.net"}],
)
api.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_app(
    routers: list[APIRouter] = [documents_app, vector_app, tools_app, tts_app]
) -> FastAPI:
    """
    Create and configure the QuipuBase API.

    Returns:
        FastAPI: The configured FastAPI application.
    """
    # for router in routers:
    #     api.include_router(router, prefix="/api")

    @api.get("/api/health")
    def _():
        return {"code": 200, "message": "QuipuBase is running!"}

    @api.get("/api/synth")
    async def _(prompt: str):
        ai = AsyncOpenAI()
        response = await ai.chat.completions.create(
            messages=[{"role": "system", "content": prompt}],
            model="llama3-8B-8192",
            max_tokens=8192,
            functions=[DataSamplingTool.definition()],
        )
        if response.choices[0].message.function_call:
            args = response.choices[0].message.function_call.arguments
            data = json.loads(args)
            return await DataSamplingTool(**data).run()
        return response.choices[0].message.content

    return api
