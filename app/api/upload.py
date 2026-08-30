import os
import uuid
import shutil

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.file_router import process_file


router = APIRouter(
    prefix="/api/v1",
    tags=["File Upload"]
)


UPLOAD_DIR = "data/uploads"

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".xlsx",
    ".xls",
    ".csv",
}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    # Validate filename
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File must have a valid filename"
        )

    # Get file extension
    file_extension = os.path.splitext(file.filename)[1].lower()

    # Validate supported file type
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_extension}"
        )

    # Create uploads directory
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Generate unique ID
    file_id = str(uuid.uuid4())

    # Create unique filename
    stored_filename = f"{file_id}{file_extension}"

    file_path = os.path.join(
        UPLOAD_DIR,
        stored_filename
    )

    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process the uploaded file
    try:
        processed_result = process_file(file_path)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File processing failed: {str(e)}"
        )

    # Return processed result
    return {
        "file_id": file_id,
        "original_filename": file.filename,
        "stored_filename": stored_filename,
        "status": "processed",
        "processing_result": processed_result
    }