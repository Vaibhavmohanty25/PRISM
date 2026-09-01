from fastapi import FastAPI

from app.api.analysis import router as analysis_router
from app.api.upload import router as upload_router
from app.services.analysis_service import AnalysisService


app = FastAPI(
    title="PRISM API",
    description="Project Reality Intelligence & Schedule Mapping",
    version="0.1.0"
)


app.include_router(upload_router)
app.include_router(analysis_router)
app.state.analysis_service = AnalysisService()


@app.get("/")
def root():
    return {
        "message": "PRISM is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "PRISM"
    }
