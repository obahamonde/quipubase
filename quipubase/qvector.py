from functools import cached_property
from typing import Literal, Optional

import hnswlib
import numpy as np
from fastapi import APIRouter, Query, Body
from numpy.typing import NDArray
from pydantic import Field
from typing_extensions import Self, TypeVar, Union

from .qdoc import Base, CosimResult, QuipuDocument, Status
from .qembed import QuipuEmbeddings

Q = TypeVar("Q", bound=QuipuDocument)


class RagRequest(Base):
    content: Union[str, list[str]]


class UpsertedCount(Base):
    upsertedCount: int


class QuipuVector(QuipuDocument):
    namespace: str = Field(
        ..., description="The namespace for the vector representation"
    )
    content: Union[str, list[str]] = Field(
        ..., description="The sentences to be encoded into vector embeddings"
    )
    value: Optional[list[float]] = Field(
        default=None, description="The computed vector embedding from the system"
    )
    top_k: int = Field(default=5, description="The number of top results to return")
    dim: Literal[384, 768] = Field(
        default=768, description="The dimension of the vector embeddings"
    )

    @cached_property
    def client(self):
        return QuipuEmbeddings()

    async def embed(self, *, namespace: str, content: Union[str, list[str]]):
        return await self.client.encode(content)

    async def query(
        self, *, namespace: str, value: NDArray[np.float32]
    ) -> list[CosimResult]:
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
        world: list[Self] = self.find_docs(limit=1000, offset=0, namespace=namespace)  # type: ignore
        if not world:
            raise ValueError("No vectors found in the namespace")
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

    async def upsert(self, *, namespace: str, content: Union[str, list[str]]):
        embeddings = await self.embed(namespace=namespace, content=content)
        instances = [
            QuipuVector(value=embedding, content=content, namespace=namespace)
            for embedding in embeddings
        ]
        count = 0
        for intance in instances:
            count += 1
            intance.put_doc()
        return UpsertedCount(upsertedCount=count)


app = APIRouter(tags=["Vector Embeddings"])


@app.post("/vector/{namespace}")
async def query_vector(
    namespace: str,
    body: RagRequest = Body(...),
    action: Literal["query", "upsert"] = Query(
        "upsert", description="The action to perform can be `query`, `upsert`"
    ),
    topK: Optional[int] = Query(
        None, description="The number of top results to return"
    ),
) -> Optional[Union[list[CosimResult], Status]]:
    """
    Query the vector representation of the content and return the top K similar results.

    Args:
        namespace (str): The namespace for the vector representation.
        action (RagAction): The action to perform.
        body (RagRequest): The request body containing the content.
        topK (int, optional): The number of top similar results to return. Defaults to 5.

    Returns:
        list[CosimResult]: A list of CosimResult objects representing the top similar results.
    """
    qvector = QuipuVector(content=body.content, top_k=topK or 5, namespace=namespace)
    if action == "query":
        return await qvector.query(
            value=await qvector.embed(namespace=namespace, content=body.content),
            namespace=namespace,
        )
    await qvector.upsert(namespace=namespace, content=body.content)
    return Status(
        code=200,
        message="Upserted successfully",
        key=qvector.key,
        definition=qvector.definition(),
    )
