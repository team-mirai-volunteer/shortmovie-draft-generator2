"""文字起こし関連のデータ構造"""

from dataclasses import dataclass
from typing import List


@dataclass
class TranscriptionSegment:
    """文字起こしの個別セグメント

    Attributes:
        start_time: 開始時刻（秒）
        end_time: 終了時刻（秒）
        text: セグメントのテキスト

    Example:
        >>> segment = TranscriptionSegment(0.0, 3.5, "こんにちは、今日は")
        >>> print(f"{segment.start_time}秒から{segment.end_time}秒: {segment.text}")
        0.0秒から3.5秒: こんにちは、今日は
    """

    start_time: float
    end_time: float
    text: str


@dataclass
class TranscriptionResult:
    """文字起こし結果の全体

    Attributes:
        segments: セグメントのリスト
        full_text: 全体のテキスト

    Example:
        >>> segments = [
        ...     TranscriptionSegment(0.0, 3.5, "こんにちは、今日は"),
        ...     TranscriptionSegment(3.5, 7.2, "ショート動画について話します")
        ... ]
        >>> result = TranscriptionResult(
        ...     segments=segments,
        ...     full_text="こんにちは、今日はショート動画について話します"
        ... )
        >>> print(f"セグメント数: {len(result.segments)}")
        セグメント数: 2
    """

    segments: List[TranscriptionSegment]
    full_text: str
