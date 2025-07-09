"""データモデルパッケージ"""

from .transcription import TranscriptionSegment, TranscriptionResult
from .draft import ShortVideoProposal, DraftResult
from .result import GenerateResult

__all__ = [
    "TranscriptionSegment",
    "TranscriptionResult",
    "ShortVideoProposal",
    "DraftResult",
    "GenerateResult",
]
