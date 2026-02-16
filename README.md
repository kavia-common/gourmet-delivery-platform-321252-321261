# gourmet-delivery-platform-321252-321261

End-to-end integration notes

- Frontend base URL
  - Set REACT_APP_API_BASE_URL in the frontend to the backend URL (for local dev, the Preview Manager URL/port of the backend).
  - Example: REACT_APP_API_BASE_URL=https://<backend-host>:<backend-port>

- Backend CORS
  - Configure ALLOWED_ORIGINS in the backend .env to the frontend origin (protocol + host + port).
  - Multiple origins supported with comma separation.
  - Example: ALLOWED_ORIGINS=http://localhost:3000

- Database connectivity (PostgreSQL)
  - The backend supports multiple ways to discover the database connection URL:
    1) POSTGRES_URL env var (SQLAlchemy URL). Example: postgresql+psycopg://user:pass@host:port/db
    2) DB_CONNECTION_FILE env var (default "db_connection.txt"). The file should contain a token with a postgresql:// URL (common pattern: "psql postgresql://..."). The backend extracts and uses it automatically.
    3) POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB/POSTGRES_PORT/POSTGRES_HOST env parts.

- Quick start (backend)
  1) Copy .env.example to .env and fill in values as needed.
  2) Install deps and run uvicorn via the Preview Manager (handled by the environment).
  3) Verify health: GET / -> {"message": "Healthy"}.

- OpenAPI
  - The backend serves OpenAPI docs and supports WebSocket help at /realtime/help.