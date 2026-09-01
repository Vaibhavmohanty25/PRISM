from typing import Any

from pydantic import BaseModel


class RootResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
    service: str


class ProjectsResponse(BaseModel):
    projects: list[str]


class UploadResponse(BaseModel):
    file_id: str
    original_filename: str
    stored_filename: str
    status: str
    processing_result: dict[str, Any]


class ErrorDetails(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetails
