from dataclasses import dataclass
from pathlib import Path
from PyPDF2 import PdfReader
from fitz import open as open_pdf  # type: ignore
from ._base import RawDoc


@dataclass
class PdfLoader(RawDoc):
    def extract_text(self):  # type: ignore
        text_doc = PdfReader(self.file_path)
        for page_number in range(len(text_doc.pages)):
            page = text_doc.pages[page_number]
            yield page.extract_text()

    def extract_image(self):
        img_doc = open_pdf(Path(self.file_path).as_posix())  # type: ignore
        for page in img_doc:  # type: ignore
            for img in page.get_images():  # type: ignore
                xref = img[0]  # type: ignore
                base_image = img_doc.extract_image(xref)  # type: ignore
                image_bytes = base_image["image"]  # type: ignore
                assert isinstance(image_bytes, bytes)
                yield image_bytes
