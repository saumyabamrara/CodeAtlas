"""CodeAtlas FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import Settings
from app.core.logging import configure_logging


def create_application(settings: Settings | None = None) -> FastAPI:
    """Create and configure the CodeAtlas API application."""
    application_settings = settings or Settings()
    configure_logging(application_settings.log_level)

    application = FastAPI(
        title=application_settings.app_name,
        version=application_settings.app_version,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=application_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router, prefix=application_settings.api_v1_prefix)
    return application


app = create_application()
