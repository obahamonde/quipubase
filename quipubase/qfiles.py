from pathlib import Path
from typing import Literal, Type
from fastapi import UploadFile
from .lib import (
    PptxLoader,
    PdfLoader,
    ExcelLoader,
    DocxLoader,
    check_suffix,
    RawDoc,
)

MapKey = Literal[".docx", ".doc", ".pdf", ".ppt", ".pptx", ".xlsx", ".xls"]

MAPPING: dict[MapKey, Type[RawDoc]] = {
    ".docx": DocxLoader,
    ".doc": DocxLoader,
    ".pdf": PdfLoader,
    ".ppt": PptxLoader,
    ".pptx": PptxLoader,
    ".xlsx": ExcelLoader,
    ".xls": ExcelLoader,
}


def stream_file(file: UploadFile, file_path: str):
    suffix = check_suffix(file)
    klass = MAPPING[suffix]
    loader = klass(file_path=Path(file_path).as_posix())
    for chunk in loader.extract_text():
        yield chunk
    for chunk in loader.extract_image():
        yield chunk
