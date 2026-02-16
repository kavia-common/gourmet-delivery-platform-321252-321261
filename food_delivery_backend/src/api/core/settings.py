import os
from functools import lru_cache
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    app_name: str = Field(default="Gourmet Delivery Platform API", description="OpenAPI title")
    app_version: str = Field(default="0.1.0", description="API version")

    # CORS
    allowed_origins: list[str] = Field(
        default_factory=lambda: os.getenv("ALLOWED_ORIGINS", "*").split(","),
        description="Comma-separated list of allowed CORS origins",
    )
    allowed_headers: list[str] = Field(
        default_factory=lambda: os.getenv("ALLOWED_HEADERS", "*").split(","),
        description="Comma-separated list of allowed CORS headers",
    )
    allowed_methods: list[str] = Field(
        default_factory=lambda: os.getenv("ALLOWED_METHODS", "*").split(","),
        description="Comma-separated list of allowed CORS methods",
    )

    # PostgreSQL (provided by the database container)
    postgres_url: str | None = Field(
        default=os.getenv("POSTGRES_URL"),
        description="SQLAlchemy-style PostgreSQL URL. If omitted, constructed from POSTGRES_* parts.",
    )
    postgres_user: str | None = Field(default=os.getenv("POSTGRES_USER"), description="PostgreSQL username")
    postgres_password: str | None = Field(default=os.getenv("POSTGRES_PASSWORD"), description="PostgreSQL password")
    postgres_db: str | None = Field(default=os.getenv("POSTGRES_DB"), description="PostgreSQL database name")
    postgres_port: str | None = Field(default=os.getenv("POSTGRES_PORT"), description="PostgreSQL port")
    postgres_host: str = Field(default=os.getenv("POSTGRES_HOST", "localhost"), description="PostgreSQL hostname")

    # Auth
    jwt_secret: str | None = Field(
        default=os.getenv("JWT_SECRET"),
        description="JWT signing secret (MUST be provided via env)",
    )
    jwt_algorithm: str = Field(default=os.getenv("JWT_ALGORITHM", "HS256"), description="JWT algorithm")
    jwt_access_token_expires_minutes: int = Field(
        default=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "60")),
        description="Access token lifetime in minutes",
    )

    # URLs
    site_url: str | None = Field(default=os.getenv("SITE_URL"), description="Frontend base URL")
    ws_url: str | None = Field(default=os.getenv("WS_URL"), description="WebSocket URL")

    def build_database_url(self) -> str:
        """Build database URL from parts if POSTGRES_URL isn't set."""
        if self.postgres_url:
            return self.postgres_url

        # Fallback to parts. Note: these are expected to be set by the orchestrator.
        if not (self.postgres_user and self.postgres_password and self.postgres_db and self.postgres_port):
            raise RuntimeError(
                "Database configuration missing. Set POSTGRES_URL or POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB/POSTGRES_PORT."
            )

        return f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings."""
    return Settings()
