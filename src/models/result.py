"""結果・レスポンス関連のデータ構造"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GenerateResult:
    """全体処理の結果

    Attributes:
        draft_file_path: 生成された企画書ファイルのパス
        subtitle_file_path: 生成された字幕ファイルのパス
        uploaded_draft_url: アップロードされた企画書のGoogle Drive URL
        uploaded_subtitle_url: アップロードされた字幕ファイルのGoogle Drive URL
        success: 処理成功フラグ
        error_message: エラーメッセージ（失敗時のみ）

    Example:
        成功時:
        >>> result = GenerateResult(
        ...     draft_file_path="output/draft.md",
        ...     subtitle_file_path="output/subtitle.srt",
        ...     success=True
        ... )
        >>> print(f"処理結果: {'成功' if result.success else '失敗'}")
        処理結果: 成功

        失敗時:
        >>> error_result = GenerateResult(
        ...     draft_file_path="",
        ...     subtitle_file_path="",
        ...     success=False,
        ...     error_message="API呼び出しに失敗しました"
        ... )
        >>> print(f"エラー: {error_result.error_message}")
        エラー: API呼び出しに失敗しました
    """

    draft_file_path: str
    subtitle_file_path: str
    success: bool
    uploaded_draft_url: Optional[str] = None
    uploaded_subtitle_url: Optional[str] = None
    error_message: Optional[str] = None
