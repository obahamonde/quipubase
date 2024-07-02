import asyncio
from functools import cached_property
from typing import Literal, Optional
import base64
from uuid import uuid4
from fastapi.responses import StreamingResponse
import hnswlib
import numpy as np
from fastapi import APIRouter, Body, Query, UploadFile, File
from numpy.typing import NDArray
from pydantic import Field
from typing_extensions import Self, TypeVar, Union
from pathlib import Path
from itertools import filterfalse, islice

from .qdoc import Base, CosimResult, QuipuDocument, Status
from .qembed import QuipuEmbeddings
from .qfiles import stream_file
from .lib import to_base64

Q = TypeVar("Q", bound=QuipuDocument)


def wrap_img(base64: str):
    return f'<img src="{base64}" style="width:100%;height:auto;">'


def b64_id():
    return base64.urlsafe_b64encode(uuid4().bytes).decode("utf-8").rstrip("=")


class RagRequest(Base):
    content: str


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
        world: list[Self] = await self.find_docs(limit=1000, offset=0, namespace=namespace)  # type: ignore
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

    async def upsert(self, *, namespace: str, request: RagRequest = Body(...)):
        embedding = await self.embed(namespace=namespace, content=request.content)
        self.value = embedding
        return await self.put_doc()

app = APIRouter(tags=["Vector Embeddings"])


@app.post("/vector/{namespace}")
async def use_embeddings(
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


    Returns:
        list[CosimResult]: A list of CosimResult objects representing the top similar results.
    """
    qvector = QuipuVector(content=body.content, top_k=topK or 5, namespace=namespace)
    if action == "query":
        return await qvector.query(
            value=await qvector.embed(namespace=namespace, content=body.content),
            namespace=namespace,
        )
    await qvector.upsert(namespace=namespace, request=body)
    return Status(
        code=200,
        message="Upserted successfully",
        key=qvector.key,
        definition=qvector.get_definition(),
    )


async def callback(chunk: str, namespace: str):
    vec = QuipuVector(content=chunk, namespace=namespace)
    vector = await vec.embed(namespace=namespace, content=chunk)
    vec.value = vector
    return (await vec.put_doc()).key


@app.post("/upload/{namespace}")
async def upload_file(namespace: str, file: UploadFile = File(...)):
    assert file.filename, "No file name provided"
    _name = b64_id() + file.filename.split(".")[-1]
    file_path = Path(f"/tmp/{_name}")
    with file_path.open("wb") as f:
        f.write(await file.read())

    async def generator():
        for instance in stream_file(
            file=file,
            file_path=file_path.as_posix(),
        ):
            if isinstance(instance, str):
                await callback(instance, namespace)
                yield instance
            if isinstance(instance, bytes):
                yield wrap_img(to_base64(instance, "png"))

    return StreamingResponse(generator(), media_type="text/html")
