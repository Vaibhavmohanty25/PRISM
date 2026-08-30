import fitz


def extract_pdf_text(file_path: str) -> str:
    """
    Extract text directly from a digital PDF.
    """

    extracted_text = []

    document = fitz.open(file_path)

    for page in document:
        page_text = page.get_text()

        if page_text.strip():
            extracted_text.append(page_text)

    document.close()

    return "\n".join(extracted_text)


def convert_pdf_to_images(file_path: str) -> list:
    """
    Convert each PDF page into an image in memory.

    Returns a list of image bytes.
    """

    document = fitz.open(file_path)
    images = []

    try:
        for page in document:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

            image_bytes = pix.tobytes("png")

            images.append(image_bytes)

    finally:
        document.close()

    return images