"""ユースケース結果関連のデータ構造"""

from dataclasses import dataclass

from .transcription import TranscriptionResult


@dataclass
class VideoToTranscriptResult:
    """動画→文字起こし処理の結果

    Attributes:
        success: 処理が成功したかどうか
        transcript_file_path: 保存されたtranscript.jsonのパス
        transcription: 文字起こし結果（成功時のみ）
        error_message: エラーメッセージ（失敗時のみ）

    Example:
        >>> result = VideoToTranscriptResult(
        ...     success=True,
        ...     transcript_file_path="intermediate/video1_transcript.json",
        ...     transcription=transcription_obj
        ... )
        >>> print(f"成功: {result.success}")
        成功: True
    """

    success: bool
    transcript_file_path: str
    transcription: TranscriptionResult | None = None
    error_message: str | None = None


@dataclass
class TranscriptToDraftResult:
    """文字起こし→企画書処理の結果

    Attributes:
        success: 処理が成功したかどうか
        draft_file_path: 生成された企画書ファイルのパス
        subtitle_file_path: 生成された字幕ファイルのパス
        transcription: 使用された文字起こし結果（成功時のみ）
        error_message: エラーメッセージ（失敗時のみ）

    Example:
        >>> result = TranscriptToDraftResult(
        ...     success=True,
        ...     draft_file_path="output/video1_draft.md",
        ...     subtitle_file_path="output/video1_subtitle.srt",
        ...     transcription=transcription_obj
        ... )
        >>> print(f"企画書: {result.draft_file_path}")
        企画書: output/video1_draft.md
    """

    success: bool
    draft_file_path: str
    subtitle_file_path: str
    transcription: TranscriptionResult | None = None
    error_message: str | None = None
