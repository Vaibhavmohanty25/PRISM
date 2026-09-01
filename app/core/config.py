from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GEMINI_API_KEY: str
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()
