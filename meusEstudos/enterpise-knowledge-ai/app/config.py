from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./local.db"
    redis_url: str = "redis://localhost:6379/0"
    session_ttl_hours: int = Field(default=24, gt=0)
    max_upload_bytes: int = Field(default=20 * 1024 * 1024, gt=0)
    max_pdf_pages: int = Field(default=200, gt=0)
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "knowledge-private"
    demo_owner_password: str = "change-me-owner"
    demo_second_owner_password: str = "change-me-owner-b"
    demo_viewer_password: str = "change-me-viewer"
    nvidia_api_key: SecretStr = SecretStr("")
    nvidia_chat_model: str = "nvidia/nemotron-3-super-120b-a12b"
    nvidia_embedding_model: str = "nvidia/nemotron-3-embed-1b"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def settings() -> Settings:
    return Settings()
