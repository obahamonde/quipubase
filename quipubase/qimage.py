from __future__ import annotations
from typing import Optional, Any
from pydantic import BaseModel, Field
from .qtools import Tool
from .qproxy import APIClient

from .qconst import HEADERS, IMAGES_URL, TIMEOUT


class ImageTool(Tool):
    """This tool should be used only when the user asks for the creation or generation of an image"""
    prompt: str = Field(..., description="The prompt to generate the image.")
    height: int = Field(default=512, gt=0)
    width: int = Field(default=512, gt=0)
    num_inference_steps: int = Field(default=20, gt=0)
    guidance_scale: float = Field(default=7.5, gt=0)
    negative_prompt: Optional[str] = Field(
        default="malformed, deformed, disgusting, gore, horror, nightmare, scary, terrifying, violence"
    )
    num_images_per_prompt: int = Field(default=1, gt=0)
    clip_skip: Optional[int] = Field(default=None)
    strength: Optional[float] = Field(default=0.75, gt=0, le=1)
    seed: Optional[int] = Field(default=None)

    async def run(self, **kwargs: Any):
        client = APIClient(base_url=IMAGES_URL, headers=HEADERS, timeout=TIMEOUT)
        data_dict = self.model_dump()
        prompt = data_dict.pop("prompt")
        payload = {"input": {"prompt": prompt}, "arguments": data_dict}
        response = await client.post(endpoint="/runsync", json=payload, headers=None)
        b_64 = ImageResponse(**response.json()).output.image_url
        return f"<img src='{b_64}'/>"


class ImageOutPut(BaseModel):
    image_url: str
    images: list[str]
    seed: int


class ImageResponse(BaseModel):
    delayTime: int
    executionTime: int
    id: str
    output: ImageOutPut
    status: str
