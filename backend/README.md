# CodeAtlas Backend

The FastAPI foundation for CodeAtlas. It provides application configuration, structured logging, development CORS, a health endpoint, and public GitHub repository cloning.

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Build the JavaParser bridge (requires JDK 8+ and Maven): `mvn -f java_parser/pom.xml package`
4. Copy `.env.example` to `.env` and adjust values if needed.
5. Start the server from this `backend` directory:

   ```bash
   uvicorn main:app --reload
   ```

Visit `http://127.0.0.1:8000/health` to receive:

```json
{
  "status": "healthy",
  "service": "CodeAtlas Backend"
}
```

Clone a public GitHub repository with `POST /repositories/clone`:

```json
{
  "repository_url": "https://github.com/owner/repository"
}
```

Repositories are cloned into `REPOSITORY_WORKSPACE` (default: `backend/workspace`).

Inspect a cloned repository with `POST /repositories/inspect`, or parse all of its
Java source files with `POST /repositories/analyze`. Both endpoints accept:

```json
{
  "local_path": "path/to/cloned/repository"
}
```

## Layout

- `main.py` creates the FastAPI application and attaches middleware and routes.
- `app/api/` composes HTTP routers; `routes/health.py` contains the health endpoint.
- `app/core/config.py` reads typed configuration from environment variables and `.env`.
- `app/core/logging.py` configures JSON structured logs using the standard library.
- `app/models/`, `schemas/`, `services/`, `analyzers/`, `database/`, and `utils/` reserve clear extension points without introducing premature implementation.
- `tests/` contains API-level tests.
