import os

from app.services.pdf_service import (
    extract_pdf_text,
    convert_pdf_to_images
)

from app.services.excel_service import extract_excel_data

from app.services.ocr_service import (
    extract_text_from_image,
    extract_text_from_bytes
)


def is_meaningful_text(
    text: str,
    minimum_characters: int = 50
) -> bool:

    if not text:
        return False

    return len(text.strip()) >= minimum_characters


def process_scanned_pdf(file_path: str) -> str:
    """
    Convert scanned PDF pages to images
    and extract text using OCR.
    """

    page_images = convert_pdf_to_images(file_path)

    extracted_pages = []

    for page_number, image_bytes in enumerate(
        page_images,
        start=1
    ):
        page_text = extract_text_from_bytes(image_bytes)

        if page_text.strip():
            extracted_pages.append(
                f"--- Page {page_number} ---\n{page_text}"
            )

    return "\n\n".join(extracted_pages)


def process_file(file_path: str) -> dict:

    file_extension = os.path.splitext(
        file_path
    )[1].lower()

    # PDF processing
    if file_extension == ".pdf":

        extracted_text = extract_pdf_text(file_path)

        # Digital PDF
        if is_meaningful_text(extracted_text):

            return {
                "file_type": "pdf",
                "document_type": "digital_pdf",
                "processing_method": "direct_text_extraction",
                "content": extracted_text
            }

        # Scanned PDF → OCR fallback
        ocr_text = process_scanned_pdf(file_path)

        return {
            "file_type": "pdf",
            "document_type": "scanned_pdf",
            "processing_method": "pdf_to_image_easyocr",
            "content": ocr_text
        }

    # Image processing
    elif file_extension in [".png", ".jpg", ".jpeg"]:

        extracted_text = extract_text_from_image(file_path)

        return {
            "file_type": "image",
            "document_type": "image",
            "processing_method": "easyocr",
            "content": extracted_text
        }

    # Excel / CSV processing
    elif file_extension in [".xlsx", ".xls", ".csv"]:

        extracted_data = extract_excel_data(file_path)

        return {
            "file_type": file_extension.replace(".", ""),
            "document_type": "structured_data",
            "processing_method": "pandas",
            "content": extracted_data
        }

    else:
        raise ValueError(
            f"Unsupported file type: {file_extension}"
        )