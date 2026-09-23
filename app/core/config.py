from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---------------------------------------------------------
    # Legacy Gemini configuration
    # ---------------------------------------------------------

    GEMINI_API_KEY: str | None = None
    GEMINI_AGENT_MODEL: str = "gemini-3.6-flash"

    # ---------------------------------------------------------
    # Groq configuration
    # ---------------------------------------------------------

    GROQ_API_KEY: str

    GROQ_AGENT_MODEL: str = "openai/gpt-oss-120b"

    GROQ_EXTRACTION_MODEL: str = "openai/gpt-oss-120b"

    # ---------------------------------------------------------
    # Upload configuration
    # ---------------------------------------------------------

    UPLOAD_DIR: str = "data/uploads"

    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024

    ALLOWED_EXTENSIONS: set[str] = {
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".xlsx",
        ".xls",
        ".csv",
    }

    # ---------------------------------------------------------
    # Environment configuration
    # ---------------------------------------------------------

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()