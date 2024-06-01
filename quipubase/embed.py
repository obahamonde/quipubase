from typing import Union, Any
from sentence_transformers import SentenceTransformer  # type: ignore
from dataclasses import dataclass, field
import numpy as np
import torch
from .proxy import Proxy
from .utils import get_device


@dataclass
class EmbeddingAPI(Proxy[SentenceTransformer]):
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

    device: str = field(default_factory=get_device)

    def __load__(self):
        return SentenceTransformer("mpnet-base-v2")

    async def encode(
        self, text: Union[str, list[str]]
    ) -> Union[np.ndarray[np.float32, Any], torch.Tensor]:
        """
        Encodes the given text into vectors.

        Args:
            text (str | list[str]): The text or list of texts to be encoded.

        Returns:
            numpy.ndarray: An array of vectors representing the encoded text.

        Example:
            embedding_api = EmbeddingAPI()
            vectors = await embedding_api.encode("Hello, world!")
        """
        return self.__as_proxied__().encode(text, device=self.device)  # type: ignore
