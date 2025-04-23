import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Dgraph settings
    dgraph_alpha_host: str = os.environ.get("DGRAPH_ALPHA_HOST", "dgraph-alpha")
    dgraph_alpha_port: str = os.environ.get("DGRAPH_ALPHA_PORT", "9080")
    dgraph_connection_timeout: int = 30  # seconds
    dgraph_pool_size: int = 10  # connection pool size
    dgraph_whitelist: str = os.environ.get("DGRAPH_WHITELIST", "172.19.0.0/16")
    dgraph_auth_token: Optional[str] = os.environ.get("DGRAPH_AUTH_TOKEN", None)

    # API settings
    api_host: str = os.environ.get("API_HOST", "0.0.0.0")
    api_port: int = int(os.environ.get("API_PORT", "8000"))
    debug: bool = os.environ.get("DEBUG", "false").lower() == "true"



    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
