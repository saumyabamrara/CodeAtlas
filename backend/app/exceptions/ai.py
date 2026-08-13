"""Stable application exceptions for model-backed architecture Q&A."""


class AIConfigurationError(RuntimeError):
    """Raised when required server-side AI configuration is missing."""


class AIProviderError(RuntimeError):
    """Raised when the configured model provider cannot return a usable answer."""


class AIProviderTimeoutError(AIProviderError):
    """Raised when the model provider exceeds the configured request timeout."""
