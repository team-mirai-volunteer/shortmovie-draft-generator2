"""Clients package for external API integrations."""

from .whisper_client import (
    WhisperClient,
    WhisperClientError,
    AudioExtractionError,
    WhisperAPIError,
    ValidationError,
)

__all__ = [
    "WhisperClient",
    "WhisperClientError",
    "AudioExtractionError",
    "WhisperAPIError",
    "ValidationError",
]
