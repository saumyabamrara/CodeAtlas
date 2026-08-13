"""Stable application exceptions for the AI architecture assistant."""


class AIConfigurationError(RuntimeError):
    """Raised when required server-side AI configuration is missing."""


class AIProviderError(RuntimeError):
    """Raised when the configured AI provider cannot return a usable answer."""


class AIProviderTimeoutError(AIProviderError):
    """Raised when the AI provider exceeds the configured request timeout."""
