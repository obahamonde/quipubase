import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Literal, Union, TypeVar

from fastapi import UploadFile
from httpx import get
from pathlib import Path


T = TypeVar("T")

Img = Union[str, bytes]


def to_base64(image: Img, suffix: str) -> str:
    if isinstance(image, bytes):
        return f"data:image/{suffix};base64,{base64.b64encode(image).decode()}"
    else:
        if Path(image).exists():
            return f"data:image/{suffix};base64,{base64.b64encode(Path(image).read_bytes()).decode()}"
        if image.startswith("http"):
            response = get(image)
            return f"data:image/{suffix};base64,{base64.b64encode(response.content).decode()}"
        if image.startswith("data:image"):
            return image
        return f"data:image/{suffix};base64,{base64.b64encode(image.encode()).decode()}"
    raise ValueError("Invalid image")


def check_suffix(
    file: UploadFile,
) -> Literal[".docx", ".pdf", ".pptx", ".xlsx"]:
    if not file.filename and not file.content_type:
        raise ValueError("Invalid file")

    if file.filename:
        if "docx" in file.filename:
            return ".docx"
        if "doc" in file.filename:
            return ".docx"
        if "pdf" in file.filename:
            return ".pdf"
        if "ppt" in file.filename:
            return ".pptx"
        if "pptx" in file.filename:
            return ".pptx"
        if "xlsx" in file.filename:
            return ".xlsx"
        if "xls" in file.filename:
            return ".xlsx"
    if file.content_type:
        if "presentation" in file.content_type:
            return ".pptx"
        if "document" in file.content_type:
            return ".docx"
        if "pdf" in file.content_type:
            return ".pdf"
        if "spreadsheet" in file.content_type:
            return ".xlsx"
    raise ValueError("Invalid file")


@dataclass
class RawDoc(ABC):
    file_path: str

    @abstractmethod
    def extract_text(self) -> Generator[str, None, None]:
        pass

    @abstractmethod
    def extract_image(self) -> Generator[bytes, None, None]:
        pass
