from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.api.routes.agent import router as agent_router
from groq import Groq
from fastapi.middleware.cors import CORSMiddleware
from app.agents.groq_adapter import GroqLLMAdapter
from app.api.analysis import router as analysis_router
from app.api.upload import router as upload_router

from app.agents.agent import ConstructionIntelligenceAgent

from app.agents.tool_registry import ToolRegistry
from app.agents.tools import PrismAgentTools

from app.core.config import settings

from app.services.analysis_service import AnalysisService
from app.schemas.api import ErrorResponse, HealthResponse, RootResponse


app = FastAPI(
    title="PRISM API",
    description="Project Reality Intelligence & Schedule Mapping",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(upload_router)
app.include_router(analysis_router)
app.include_router(
    agent_router,
    prefix="/api/v1",
)


# ---------------------------------------------------------------------
# Shared application services
# ---------------------------------------------------------------------

analysis_service = AnalysisService()

agent_tools = PrismAgentTools(
    analysis_service
)

tool_registry = ToolRegistry(
    agent_tools
)

groq_client = Groq(
    api_key=settings.GROQ_API_KEY
)

groq_adapter = GroqLLMAdapter(
    client=groq_client,
    model=settings.GROQ_AGENT_MODEL,
)

construction_agent = ConstructionIntelligenceAgent(
    llm=groq_adapter,
    registry=tool_registry,
)

# ---------------------------------------------------------------------
# FastAPI application state
# ---------------------------------------------------------------------

app.state.analysis_service = analysis_service
app.state.agent = construction_agent


@app.get("/", response_model=RootResponse)
def root() -> RootResponse:
    return {
        "message": "PRISM is running"
    }


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return {
        "status": "healthy",
        "service": "PRISM"
    }


def _error_payload(code: str, message: str) -> dict:
    return ErrorResponse(
        error={
            "code": code,
            "message": message,
        }
    ).model_dump()


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    del request

    missing_file = any(
        error.get("loc", ())[-1:] == ("file",)
        and error.get("type") == "missing"
        for error in exc.errors()
    )

    if missing_file:
        code = "missing_file"
        message = "An upload file is required"
    else:
        code = "invalid_request"
        message = "Request validation failed"

    return JSONResponse(
        status_code=400,
        content=_error_payload(
            code,
            message,
        ),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    del request

    detail = exc.detail

    if isinstance(detail, dict):
        code = detail.get(
            "code",
            "http_error",
        )
        message = detail.get(
            "message",
            "Request failed",
        )

    else:
        message = str(detail)

        if message.startswith(
            "Unknown project:"
        ):
            code = "project_not_found"

        elif message.startswith(
            "Unknown activity:"
        ):
            code = "activity_not_found"

        else:
            code = "http_error"

    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(
            code,
            message,
        ),
    )