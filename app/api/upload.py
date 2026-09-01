import os
import uuid

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
)
from pydantic import ValidationError

from app.schemas.project_data import ProgressReport
from app.services.analysis_service import (
    AnalysisService,
    get_analysis_service,
)
from app.services.file_router import process_file
from app.core.config import settings
from app.schemas.api import UploadResponse


router = APIRouter(
    prefix="/api/v1",
    tags=["File Upload"]
)


UPLOAD_DIR = settings.UPLOAD_DIR
MAX_UPLOAD_SIZE_BYTES = settings.MAX_UPLOAD_SIZE_BYTES

ALLOWED_EXTENSIONS = settings.ALLOWED_EXTENSIONS


@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    analysis_service: AnalysisService = Depends(
        get_analysis_service
    ),
)-> UploadResponse:

    # Validate filename
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_filename",
                "message": "File must have a valid filename",
            },
        )

    contents = await file.read(MAX_UPLOAD_SIZE_BYTES + 1)
    if not contents:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "empty_file",
                "message": "Uploaded file must not be empty",
            },
        )
    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail={
                "code": "file_too_large",
                "message": "Uploaded file exceeds the maximum size",
            },
        )

    # Get file extension
    file_extension = os.path.splitext(file.filename)[1].lower()

    # Validate supported file type
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "unsupported_file_type",
                "message": "Uploaded file type is not supported",
            },
        )

    # Generate unique ID
    file_id = str(uuid.uuid4())

    # Create unique filename
    stored_filename = f"{file_id}{file_extension}"

    file_path = os.path.join(
        UPLOAD_DIR,
        stored_filename
    )

    succeeded = False
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        with open(file_path, "wb") as buffer:
            buffer.write(contents)

        processed_result = process_file(file_path)

        extracted_data = processed_result.get(
            "extracted_data"
        )
        if isinstance(extracted_data, dict) and "activities" in extracted_data:
            analysis_service.record_report(
                ProgressReport.model_validate(extracted_data)
            )

        response = UploadResponse(
            file_id=file_id,
            original_filename=file.filename,
            stored_filename=stored_filename,
            status="processed",
            processing_result=processed_result,
        )
        succeeded = True
        return response
    except ValidationError:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_extracted_data",
                "message": "Extracted data did not match the report schema",
            },
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_file",
                "message": "Uploaded file could not be processed",
            },
        )
    except OSError:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "file_save_failed",
                "message": "Uploaded file could not be saved",
            },
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "processing_failed",
                "message": "File processing failed",
            },
        )
    finally:
        if not succeeded:
            try:
                os.remove(file_path)
            except FileNotFoundError:
                pass
