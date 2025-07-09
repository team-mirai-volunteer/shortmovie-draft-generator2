"""Whisper APIクライアントモジュール"""

import os
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, Any
import ffmpeg
from openai import OpenAI

from ..models.transcription import TranscriptionSegment, TranscriptionResult


class WhisperClientError(Exception):
    """WhisperClient関連のベース例外"""

    pass


class AudioExtractionError(WhisperClientError):
    """音声抽出エラー"""

    def __init__(
        self, message: str, video_path: str, ffmpeg_error: Optional[str] = None
    ):
        super().__init__(message)
        self.video_path = video_path
        self.ffmpeg_error = ffmpeg_error


class WhisperAPIError(WhisperClientError):
    """Whisper API呼び出しエラー"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        retry_after: Optional[int] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


class ValidationError(WhisperClientError):
    """レスポンス内容検証エラー"""

    def __init__(self, message: str, field_name: Optional[str] = None):
        super().__init__(message)
        self.field_name = field_name


class WhisperClient:
    """Whisper APIクライアント

    動画ファイルから音声を抽出し、Whisper APIで文字起こしを実行します。
    タイムスタンプ付きのセグメント情報を含むTranscriptionResultを生成します。

    Example:
        >>> client = WhisperClient("your-api-key")
        >>> result = client.transcribe("input/video.mp4")
        >>> print(f"セグメント数: {len(result.segments)}")
        セグメント数: 15
        >>> print(f"全体テキスト長: {len(result.full_text)}")
        全体テキスト長: 1250
    """

    def __init__(
        self, api_key: str, model: str = "whisper-1", temp_dir: Optional[str] = None
    ) -> None:
        """WhisperClientを初期化

        Args:
            api_key: OpenAI APIキー
            model: 使用するWhisperモデル
            temp_dir: 一時ファイル保存ディレクトリ

        Raises:
            ValueError: APIキーが無効な場合
            OSError: 一時ディレクトリの作成に失敗した場合
        """
        if not api_key or not api_key.strip():
            raise ValueError("APIキーが指定されていません")

        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=api_key)

        if temp_dir:
            self.temp_dir = Path(temp_dir)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
        else:
            # プロジェクトルートのintermediateディレクトリを使用
            self.temp_dir = Path("intermediate")
            self.temp_dir.mkdir(parents=True, exist_ok=True)

    def transcribe(self, video_path: str) -> TranscriptionResult:
        """動画ファイルから文字起こしを実行

        Args:
            video_path: 動画ファイルのパス

        Returns:
            文字起こし結果（TranscriptionResult）

        Raises:
            FileNotFoundError: 動画ファイルが存在しない場合
            AudioExtractionError: 音声抽出に失敗した場合
            WhisperAPIError: Whisper API呼び出しに失敗した場合
            ValidationError: レスポンス内容が期待する形式でない場合
        """
        self._validate_video_file(video_path)

        audio_path = None
        try:
            audio_path = self._extract_audio(video_path)
            response_data = self._call_whisper_api(audio_path)
            self._validate_response_data(response_data)
            return self._convert_to_transcription_result(response_data)

        finally:
            # デバッグのため、音声ファイルは削除しない
            # if audio_path:
            #     self._cleanup_temp_files(audio_path)
            pass

    def _validate_video_file(self, video_path: str) -> None:
        """動画ファイルの妥当性チェック"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"動画ファイルが見つかりません: {video_path}")

        file_size = os.path.getsize(video_path)
        max_size = 25 * 1024 * 1024
        # if file_size > max_size:
        #     raise ValidationError(
        #         f"ファイルサイズが制限を超えています: {file_size / 1024 / 1024:.1f}MB > 25MB"
        #     )

        allowed_extensions = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}
        file_extension = Path(video_path).suffix.lower()
        if file_extension not in allowed_extensions:
            raise ValidationError(f"サポートされていないファイル形式です: {file_extension}")

    def _extract_audio(self, video_path: str) -> str:
        """動画ファイルから音声を抽出

        Args:
            video_path: 動画ファイルのパス

        Returns:
            抽出された音声ファイルのパス

        Raises:
            AudioExtractionError: 音声抽出に失敗した場合
        """
        try:
            video_name = Path(video_path).stem
            audio_path = self.temp_dir / f"{video_name}_audio.mp3"

            print(f"DEBUG: 動画ファイル: {video_path}")
            print(f"DEBUG: 動画ファイルサイズ: {os.path.getsize(video_path) / 1024 / 1024:.1f}MB")
            print(f"DEBUG: 音声抽出先: {audio_path}")

            # MP3形式で抽出（64kbps、モノラル、16kHz）
            (
                ffmpeg.input(video_path)
                .output(str(audio_path), acodec="mp3", ac=1, ar=16000, audio_bitrate="64k")
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            if not audio_path.exists():
                raise AudioExtractionError(
                    f"音声ファイルの生成に失敗しました: {audio_path}", video_path
                )

            audio_size = os.path.getsize(str(audio_path))
            print(f"DEBUG: 抽出された音声ファイルサイズ: {audio_size / 1024 / 1024:.1f}MB")

            # Whisper APIの制限チェック（25MB）
            max_size = 25 * 1024 * 1024
            if audio_size > max_size:
                raise AudioExtractionError(
                    f"抽出された音声ファイルがWhisper APIの制限を超えています: {audio_size / 1024 / 1024:.1f}MB > 25MB",
                    video_path
                )

            return str(audio_path)

        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if e.stderr else str(e)
            raise AudioExtractionError(
                f"ffmpegによる音声抽出に失敗しました: {error_message}",
                video_path,
                ffmpeg_error=error_message,
            )
        except Exception as e:
            raise AudioExtractionError(f"音声抽出中に予期しないエラーが発生しました: {str(e)}", video_path)

    def _call_whisper_api(
        self, audio_path: str, max_retries: int = 3
    ) -> Dict[str, Any]:
        """リトライ機能付きWhisper API呼び出し

        Args:
            audio_path: 音声ファイルのパス
            max_retries: 最大リトライ回数

        Returns:
            Whisper APIからのレスポンスデータ

        Raises:
            WhisperAPIError: API呼び出しに失敗した場合
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                with open(audio_path, "rb") as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model=self.model,
                        file=audio_file,
                        response_format="verbose_json",
                        timestamp_granularities=["segment"],
                    )

                return response.model_dump()

            except Exception as e:
                last_exception = e

                if hasattr(e, "status_code") and getattr(e, "status_code") == 429:
                    retry_after = getattr(e, "retry_after", 60)
                    if attempt < max_retries - 1:
                        time.sleep(retry_after)
                        continue

                if attempt < max_retries - 1:
                    time.sleep(2**attempt)

        raise WhisperAPIError(
            f"Whisper API呼び出しが{max_retries}回失敗しました: {str(last_exception)}"
        )

    def _validate_response_data(self, data: Dict[str, Any]) -> None:
        """レスポンスデータの検証

        Args:
            data: Whisper APIからのレスポンスデータ

        Raises:
            ValidationError: レスポンス内容が期待する形式でない場合
        """
        if "text" not in data:
            raise ValidationError("レスポンスに'text'フィールドがありません")

        if "segments" not in data:
            raise ValidationError("レスポンスに'segments'フィールドがありません")

        if not isinstance(data["segments"], list):
            raise ValidationError("'segments'フィールドがリスト形式ではありません")

        required_segment_fields = ["start", "end", "text"]
        for i, segment in enumerate(data["segments"]):
            for field in required_segment_fields:
                if field not in segment:
                    raise ValidationError(
                        f"セグメント{i}に必須フィールド'{field}'がありません", field_name=field
                    )

    def _convert_to_transcription_result(
        self, data: Dict[str, Any]
    ) -> TranscriptionResult:
        """APIレスポンスをTranscriptionResultオブジェクトに変換

        Args:
            data: Whisper APIからのレスポンスデータ

        Returns:
            TranscriptionResult オブジェクト
        """
        segments = []
        for segment_data in data["segments"]:
            segment = TranscriptionSegment(
                start_time=float(segment_data["start"]),
                end_time=float(segment_data["end"]),
                text=segment_data["text"].strip(),
            )
            segments.append(segment)

        return TranscriptionResult(segments=segments, full_text=data["text"].strip())

    def _cleanup_temp_files(self, *file_paths: str) -> None:
        """一時ファイルのクリーンアップ

        Args:
            *file_paths: クリーンアップ対象のファイルパス
        """
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except OSError:
                pass
