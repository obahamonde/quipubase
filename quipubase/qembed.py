import os

import numpy as np
from httpx import AsyncClient

from .qproxy import QProxy


class EmbeddingAPI(QProxy[AsyncClient]):
    """
    A class that provides an API for encoding text into vectors using an asynchronous client.

    Attributes:
        None

    Methods:
        __load__(): Loads the asynchronous client.
        encode(text: str | list[str]): Encodes the given text into vectors.

    Usage:
        embedding_api = EmbeddingAPI()
        vectors = await embedding_api.encode("Hello, world!")
    """

    def __load__(self):
        return AsyncClient(
            timeout=60,
        )

    async def encode(self, text: str | list[str]):
        """
                Encodes the given text into vectors.

                Args:
                    text (str | list[str]): The text or list of texts to be encoded.
        w
                Returns:
                    numpy.ndarray: An array of vectors representing the encoded text.

                Example:
                    embedding_api = EmbeddingAPI()
                    vectors = await embedding_api.encode("Hello, world!")
        """
        if isinstance(text, str):
            text = [text]
        response = await self.__load__().post(
            os.environ.get("http://embeddings.indiecloud/embeddings", ""),
            json={"content": text},
        )
        vector = response.json()["content"]
        return np.array(vector, np.float32)  # type: ignore
