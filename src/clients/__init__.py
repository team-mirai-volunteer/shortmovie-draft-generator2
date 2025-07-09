"""Clients package for external API integrations."""

from .whisper_client import (
    WhisperClient,
    WhisperClientError,
    AudioExtractionError,
    WhisperAPIError,
    ValidationError,
)
from .chatgpt_client import (
    ChatGPTClient,
    ChatGPTClientError,
    ChatGPTAPIError,
    JSONParseError,
    ValidationError as ChatGPTValidationError,
)

__all__ = [
    "WhisperClient",
    "WhisperClientError",
    "AudioExtractionError",
    "WhisperAPIError",
    "ValidationError",
    "ChatGPTClient",
    "ChatGPTClientError",
    "ChatGPTAPIError",
    "JSONParseError",
    "ChatGPTValidationError",
]
