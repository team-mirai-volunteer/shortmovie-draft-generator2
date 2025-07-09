"""企画書関連のデータ構造"""

from dataclasses import dataclass
from typing import List
from .transcription import TranscriptionResult


@dataclass
class ShortVideoProposal:
    """ショート動画の企画提案

    Attributes:
        title: 動画タイトル
        start_time: 切り抜き開始時刻（秒）
        end_time: 切り抜き終了時刻（秒）
        caption: キャプション
        key_points: キーポイントのリスト

    Example:
        >>> proposal = ShortVideoProposal(
        ...     title="面白いトーク集",
        ...     start_time=30.0,
        ...     end_time=90.0,
        ...     caption="今日の面白い話をまとめました！",
        ...     key_points=["ポイント1", "ポイント2"]
        ... )
        >>> print(f"タイトル: {proposal.title}")
        タイトル: 面白いトーク集
    """

    title: str
    start_time: float
    end_time: float
    caption: str
    key_points: List[str]


@dataclass
class DraftResult:
    """企画書生成結果

    Attributes:
        proposals: 企画提案のリスト
        original_transcription: 元の文字起こし結果

    Example:
        >>> from .transcription import TranscriptionSegment, TranscriptionResult
        >>> segments = [TranscriptionSegment(0.0, 10.0, "テスト")]
        >>> transcription = TranscriptionResult(segments, "テスト")
        >>> proposals = [
        ...     ShortVideoProposal("タイトル1", 0.0, 5.0, "キャプション1", ["ポイント1"])
        ... ]
        >>> draft = DraftResult(proposals, transcription)
        >>> print(f"提案数: {len(draft.proposals)}")
        提案数: 1
    """

    proposals: List[ShortVideoProposal]
    original_transcription: TranscriptionResult
