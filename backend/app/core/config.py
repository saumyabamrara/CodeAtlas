"""Application configuration loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings for the CodeAtlas API."""

    app_name: str = "CodeAtlas Backend"
    app_version: str = "0.1.0"
    api_v1_prefix: str = ""
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    repository_workspace: Path = BASE_DIR / "workspace"
    java_parser_runner_jar: Path = (
        BASE_DIR / "java_parser" / "target" / "codeatlas-java-parser-runner.jar"
    )
    java_executable: str = "java"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
