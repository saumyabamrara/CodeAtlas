"""Structured logging configuration for the application."""

import json
import logging
from datetime import UTC, datetime
from typing import Any


_LOG_RECORD_ATTRIBUTES = frozenset(logging.makeLogRecord({}).__dict__) | {
    "asctime",
    "message",
}


class JsonFormatter(logging.Formatter):
    """Render standard library log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialize a log record without relying on external logging packages."""
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        payload.update(
            {
                field: value
                for field, value in record.__dict__.items()
                if field not in _LOG_RECORD_ATTRIBUTES and field not in payload
            }
        )
        return json.dumps(payload, default=str)


def configure_logging(log_level: str) -> None:
    """Configure application logging once during application creation."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())
