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
        description="SQLAlchemy-style PostgreSQL URL. If omitted, can be read from DB_CONNECTION_FILE or constructed from POSTGRES_* parts.",
    )
    postgres_user: str | None = Field(default=os.getenv("POSTGRES_USER"), description="PostgreSQL username")
    postgres_password: str | None = Field(default=os.getenv("POSTGRES_PASSWORD"), description="PostgreSQL password")
    postgres_db: str | None = Field(default=os.getenv("POSTGRES_DB"), description="PostgreSQL database name")
    postgres_port: str | None = Field(default=os.getenv("POSTGRES_PORT"), description="PostgreSQL port")
    postgres_host: str = Field(default=os.getenv("POSTGRES_HOST", "localhost"), description="PostgreSQL hostname")
    db_connection_file: str = Field(
        default=os.getenv("DB_CONNECTION_FILE", "db_connection.txt"),
        description="Path to db_connection.txt file (first token containing postgresql URL will be used).",
    )

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

    def _normalize_sqlalchemy_url(self, url: str) -> str:
        """
        Ensure the SQLAlchemy URL uses the psycopg driver.
        Accepts either postgresql:// or postgresql+psycopg:// and returns postgresql+psycopg://...
        """
        if url.startswith("postgresql+psycopg://"):
            return url
        if url.startswith("postgresql://"):
            return "postgresql+psycopg://" + url[len("postgresql://") :]
        # Leave other schemes untouched (in case of future adapters)
        return url

    def _read_db_url_from_file(self) -> str | None:
        """
        Try to read a PostgreSQL URL from db_connection.txt-formatted file.
        Expected content example (first token used):
            psql postgresql://user:pass@host:port/db
        """
        path = self.db_connection_file
        try:
            if not os.path.exists(path):
                return None
            with open(path, "r") as f:
                content = f.read().strip()
            # Split by whitespace and newlines to find a token that looks like a postgresql URL
            for token in content.replace("\n", " ").split():
                if token.startswith("postgresql://") or token.startswith("postgresql+psycopg://"):
                    return self._normalize_sqlalchemy_url(token)
        except Exception:
            # Silent fallback - callers will handle raising if nothing configured
            return None
        return None

    # PUBLIC_INTERFACE
    def build_database_url(self) -> str:
        """Build database URL from POSTGRES_URL, DB_CONNECTION_FILE, or parts (POSTGRES_*)."""
        if self.postgres_url:
            return self._normalize_sqlalchemy_url(self.postgres_url)

        # Try db_connection.txt pattern
        file_url = self._read_db_url_from_file()
        if file_url:
            return file_url

        # Fallback to parts. Note: these are expected to be set by the orchestrator.
        if not (self.postgres_user and self.postgres_password and self.postgres_db and self.postgres_port):
            raise RuntimeError(
                "Database configuration missing. Provide one of: "
                "POSTGRES_URL, DB_CONNECTION_FILE pointing to db_connection.txt, "
                "or POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB/POSTGRES_PORT."
            )

        return f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings."""
    return Settings()
