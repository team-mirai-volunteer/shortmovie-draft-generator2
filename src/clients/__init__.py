"""Clients package for external API integrations."""

from .whisper_client import (
    AudioExtractionError,
    ValidationError,
    WhisperAPIError,
    WhisperClient,
    WhisperClientError,
)

__all__ = [
    "AudioExtractionError",
    "ValidationError",
    "WhisperAPIError",
    "WhisperClient",
    "WhisperClientError",
]
