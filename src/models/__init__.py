"""データモデルパッケージ"""

from .draft import DraftResult, ShortVideoProposal
from .result import GenerateResult
from .transcription import TranscriptionResult, TranscriptionSegment

__all__ = [
    "DraftResult",
    "GenerateResult",
    "ShortVideoProposal",
    "TranscriptionResult",
    "TranscriptionSegment",
]
