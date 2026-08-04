# CodeAtlas Backend

The FastAPI foundation for CodeAtlas. It currently provides application configuration, structured logging, development CORS, and a health endpoint only.

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and adjust values if needed.
4. Start the server from this `backend` directory:

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

## Layout

- `main.py` creates the FastAPI application and attaches middleware and routes.
- `app/api/` composes HTTP routers; `routes/health.py` contains the health endpoint.
- `app/core/config.py` reads typed configuration from environment variables and `.env`.
- `app/core/logging.py` configures JSON structured logs using the standard library.
- `app/models/`, `schemas/`, `services/`, `analyzers/`, `database/`, and `utils/` reserve clear extension points without introducing premature implementation.
- `tests/` contains API-level tests.
