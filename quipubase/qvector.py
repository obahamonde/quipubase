import asyncio
from functools import cached_property
from typing import Literal

import hnswlib
import numpy as np
from fastapi import APIRouter
from numpy.typing import NDArray
from pydantic import BaseModel, Field
from typing_extensions import Self, TypeVar

from .qdoc import Embedding, QDocument
from .qembed import EmbeddingAPI

Q = TypeVar("Q", bound=QDocument)


class CosimResult(BaseModel):
    id: str
    score: float
    content: str | list[str]


class QVRequest(BaseModel):
    content: str | list[str]


class QVector(Embedding):
    content: str | list[str] = Field(
        ..., description="The sentences to be encoded into vector embeddings"
    )
    namespace: str = Field(..., description="The namespace of the user/org")
    value: list[float] | None = Field(
        default=None, description="The computed vector embedding from the system"
    )
    top_k: int = Field(default=5, description="The number of top results to return")
    dim: Literal[384] = Field(
        default=384, description="The dimension of the vector embeddings"
    )

    @cached_property
    def client(self):
        return EmbeddingAPI()

    async def embed(self, *, content: str | list[str]):
        return await self.client.encode(content)

    async def query(self, *, value: NDArray[np.float32]) -> list[CosimResult]:
        """
        Cosine similarity search
        * value: the query vector
        * returns: a list of CosimResult

        **Steps**
        1. Get all the vectors from the namespace
        2. Create a hnswlib index and add all the vectors to it
        3. Query the index with the query vector
        4. Return the top k results

        """
        if asyncio.iscoroutinefunction(
            self.find_docs(1000, 0, namespace=self.namespace)
        ):
            world: list[Self] = await self.find_docs(limit=1000, offset=0, namespace=self.namespace)  # type: ignore
        else:
            world: list[Self] = self.find_docs(limit=1000, offset=0, namespace=self.namespace)  # type: ignore
        if not world:
            return []
        p = hnswlib.Index(space="cosine", dim=self.dim)  # type: ignore
        p.init_index(max_elements=len(world), ef_construction=200, M=16)  # type: ignore
        p.set_ef(50)  # type: ignore
        items = [doc.value for doc in world]  # type: ignore
        p.add_items(items)  # type: ignore
        labels, distances = p.knn_query(value, k=min(self.top_k, len(world)))  # type: ignore
        world = [world[label] for label in labels[0]]  # type: ignore
        return [
            {
                "score": 1 - distance,
                "content": world[i].content,
                "id": world[i].key,
            }  # type: ignore
            for i, distance in enumerate(distances[0])  # type: ignore
        ]

    async def upsert(self, *, content: str | list[str]):
        embeddings = await self.embed(content=content)
        instances = [
            QVector(namespace=self.namespace, value=embedding, content=content)
            for embedding in embeddings
        ]
        for intance in instances:
            intance.put_doc()


app = APIRouter(prefix="/api/qvector")


@app.post("/search/{namespace}")
async def query_vector(
    namespace: str, body: QVRequest, topK: int | None
) -> list[CosimResult]:
    qvector = QVector(content=body.content, namespace=namespace, top_k=topK or 5)
    return await qvector.query(value=await qvector.embed(content=body.content))


@app.post("/upsert/{namespace}")
async def upsert_vector(namespace: str, body: QVRequest):
    qvector = QVector(content=body.content, namespace=namespace)
    return await qvector.upsert(content=body.content)
