import easyocr
import numpy as np
import cv2


# Load the OCR model once
reader = easyocr.Reader(
    ["en"],
    gpu=False
)


def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from an image file.
    """

    results = reader.readtext(
        image_path,
        detail=0
    )

    return "\n".join(results)


def extract_text_from_bytes(image_bytes: bytes) -> str:
    """
    Extract text from image bytes.
    Used for PDF pages converted into PNG images.
    """

    image_array = np.frombuffer(
        image_bytes,
        dtype=np.uint8
    )

    image = cv2.imdecode(
        image_array,
        cv2.IMREAD_COLOR
    )

    if image is None:
        raise ValueError("Could not decode image bytes")

    results = reader.readtext(
        image,
        detail=0
    )

    return "\n".join(results)