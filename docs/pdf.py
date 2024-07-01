import fitz
import base64
import PyPDF2 as pdf2

path = "./doc.pdf"

def image_gen(file:str):
	pdf_file = fitz.open(file)
	for page_number in range(len(pdf_file)):
		page = pdf_file[page_number]

		for img in page.get_images():
			xref = img[0]
			base_image = pdf_file.extract_image(xref)
			image_bytes = base_image["image"]
			assert isinstance(image_bytes, bytes)
			image_ext = base_image["ext"]
			assert isinstance(image_ext, str)
			yield f"<img src='data:image/{image_ext};base64,{base64.b64encode(image_bytes).decode()}' />"

def text_gen(file:str):
	pdf_file = pdf2.PdfFileReader(file)
	for page_number in range(pdf_file.getNumPages()):
		page = pdf_file.getPage(page_number)
		yield page.extract_text()