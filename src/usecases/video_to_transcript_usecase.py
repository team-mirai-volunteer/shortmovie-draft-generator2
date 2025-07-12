"""動画→文字起こしユースケース"""

import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from ..clients.whisper_client import WhisperClient
from ..models.transcription import TranscriptionResult
from ..models.usecase_results import VideoToTranscriptResult


class VideoToTranscriptUsecaseError(Exception):
    """VideoToTranscriptUsecase関連のベース例外"""


class VideoInputValidationError(VideoToTranscriptUsecaseError):
    """動画入力検証エラー"""

    def __init__(self, message: str, field_name: str | None = None):
        super().__init__(message)
        self.field_name = field_name


class TranscriptionProcessError(VideoToTranscriptUsecaseError):
    """文字起こし処理エラー"""

    def __init__(self, message: str, video_path: str | None = None):
        super().__init__(message)
        self.video_path = video_path


class VideoToTranscriptUsecase:
    """動画ファイルから文字起こしを実行し、中間ファイルに保存するユースケース

    責務:
    - 動画ファイルの入力検証
    - Whisper APIによる文字起こし実行
    - 文字起こし結果をintermediate/{video_name}_transcript.jsonに保存
    - エラーハンドリング

    Example:
        >>> usecase = VideoToTranscriptUsecase(whisper_client)
        >>> result = usecase.execute("input/video.mp4")
        >>> if result.success:
        ...     print(f"文字起こし完了: {result.transcript_file_path}")
        文字起こし完了: intermediate/video_transcript.json

    """

    def __init__(self, whisper_client: WhisperClient):
        """VideoToTranscriptUsecaseを初期化

        Args:
            whisper_client: Whisper APIクライアント

        """
        self.whisper_client = whisper_client

    def execute(self, video_path: str, intermediate_dir: str = "intermediate") -> VideoToTranscriptResult:
        """動画から文字起こしを実行し、JSONファイルに保存

        Args:
            video_path: 動画ファイルのパス
            intermediate_dir: 中間ファイル保存ディレクトリ（デフォルト: "intermediate"）

        Returns:
            処理結果（VideoToTranscriptResult）

        """
        try:
            # 1. 入力検証
            self._validate_input(video_path, intermediate_dir)

            # 2. 出力ディレクトリ準備
            self._prepare_intermediate_directory(intermediate_dir)

            # 3. 文字起こし実行
            transcription = self.whisper_client.transcribe(video_path)

            # 4. 中間ファイルに保存
            transcript_file_path = self._save_transcript(transcription, video_path, intermediate_dir)

            return VideoToTranscriptResult(success=True, transcript_file_path=transcript_file_path, transcription=transcription)

        except Exception as e:
            return VideoToTranscriptResult(success=False, transcript_file_path="", error_message=str(e))

    def _validate_input(self, video_path: str, intermediate_dir: str) -> None:
        """入力パラメータの検証

        Args:
            video_path: 動画ファイルのパス
            intermediate_dir: 中間ファイル保存ディレクトリ

        Raises:
            VideoInputValidationError: 入力が無効な場合

        """
        if not video_path or not video_path.strip():
            raise VideoInputValidationError("動画ファイルパスが指定されていません", "video_path")

        if not os.path.exists(video_path):
            raise VideoInputValidationError(f"動画ファイルが存在しません: {video_path}", "video_path")

        if not os.path.isfile(video_path):
            raise VideoInputValidationError(f"指定されたパスはファイルではありません: {video_path}", "video_path")

        if not intermediate_dir or not intermediate_dir.strip():
            raise VideoInputValidationError("中間ディレクトリが指定されていません", "intermediate_dir")

        # サポートされている動画形式の確認
        allowed_extensions = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}
        file_extension = Path(video_path).suffix.lower()
        if file_extension not in allowed_extensions:
            raise VideoInputValidationError(f"サポートされていないファイル形式です: {file_extension}", "video_path")

    def _prepare_intermediate_directory(self, intermediate_dir: str) -> None:
        """中間ファイル保存ディレクトリの準備

        Args:
            intermediate_dir: 中間ファイル保存ディレクトリ

        Raises:
            TranscriptionProcessError: ディレクトリ作成に失敗した場合

        """
        try:
            intermediate_path = Path(intermediate_dir)
            intermediate_path.mkdir(parents=True, exist_ok=True)

            if not intermediate_path.is_dir():
                raise TranscriptionProcessError(f"中間ディレクトリの作成に失敗しました: {intermediate_dir}")

        except Exception as e:
            raise TranscriptionProcessError(f"中間ディレクトリの準備に失敗しました: {e!s}") from e

    def _save_transcript(self, transcription: TranscriptionResult, video_path: str, intermediate_dir: str) -> str:
        """文字起こし結果をJSONファイルに保存

        Args:
            transcription: 保存する文字起こし結果
            video_path: 元の動画ファイルパス
            intermediate_dir: 中間ファイル保存ディレクトリ

        Returns:
            保存されたファイルのパス

        Raises:
            TranscriptionProcessError: ファイル保存に失敗した場合

        """
        try:
            intermediate_path = Path(intermediate_dir)
            video_name = Path(video_path).stem
            transcript_file = intermediate_path / f"{video_name}_transcript.json"

            # 文字起こし結果をシリアライズ
            data = self._serialize_transcription(transcription, video_path)

            with open(transcript_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return str(transcript_file)

        except Exception as e:
            raise TranscriptionProcessError(f"文字起こし結果の保存に失敗しました: {e!s}") from e

    def _serialize_transcription(self, transcription: TranscriptionResult, video_path: str) -> dict:
        """TranscriptionResultをシリアライズ可能な辞書に変換

        Args:
            transcription: シリアライズする文字起こし結果
            video_path: 元の動画ファイルパス

        Returns:
            シリアライズされた辞書

        """
        return {
            "video_name": Path(video_path).name,
            "video_path": video_path,
            "created_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
            "full_text": transcription.full_text,
            "segments": [
                {
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
                    "text": segment.text,
                }
                for segment in transcription.segments
            ],
        }
