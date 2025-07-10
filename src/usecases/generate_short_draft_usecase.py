"""ショート動画企画書生成ユースケース"""

import os
from pathlib import Path
from typing import Optional

from ..models.result import GenerateResult
from ..models.draft import DraftResult
from ..service.draft_generator import DraftGenerator
from ..service.srt_generator import SrtGenerator
from ..clients.google_drive_client import GoogleDriveClient, FileUploadError
from ..sources.google_drive_video_source import GoogleDriveVideoSource


class GenerateShortDraftUsecaseError(Exception):
    """GenerateShortDraftUsecase関連のベース例外"""

    pass


class InputValidationError(GenerateShortDraftUsecaseError):
    """入力検証エラー"""

    def __init__(self, message: str, field_name: Optional[str] = None):
        super().__init__(message)
        self.field_name = field_name


class OutputGenerationError(GenerateShortDraftUsecaseError):
    """出力ファイル生成エラー"""

    def __init__(self, message: str, file_path: Optional[str] = None):
        super().__init__(message)
        self.file_path = file_path


class GenerateShortDraftUsecase:
    """ショート動画企画書生成ユースケース

    動画ファイルを入力として、企画書（Markdown）と字幕ファイル（SRT）を生成します。
    入力検証、出力ファイル管理、エラーハンドリングを含む全体フロー制御を行います。

    Example:
        >>> usecase = GenerateShortDraftUsecase(draft_generator)
        >>> result = usecase.execute("input/video.mp4", "output/")
        >>> if result.success:
        ...     print(f"企画書: {result.draft_file_path}")
        ...     print(f"字幕: {result.subtitle_file_path}")
        企画書: output/video_draft.md
        字幕: output/video_subtitle.srt
    """

    def __init__(
        self,
        draft_generator: DraftGenerator,
        srt_generator: SrtGenerator,
        google_drive_client: GoogleDriveClient,
        upload_enabled: bool = False,
        upload_folder_id: Optional[str] = None,
    ):
        """GenerateShortDraftUsecaseを初期化

        Args:
            draft_generator: 企画書生成サービス
            srt_generator: SRT字幕ファイル生成サービス
            google_drive_client: Google Driveクライアント（DIContainerから注入）
            upload_enabled: Google Driveアップロードを有効にするかどうか
            upload_folder_id: アップロード先のGoogle DriveフォルダID
        """
        self.draft_generator = draft_generator
        self.srt_generator = srt_generator
        self.google_drive_client = google_drive_client
        self.upload_enabled = upload_enabled
        self.upload_folder_id = upload_folder_id

    def execute(self, video_path: str, output_dir: str) -> GenerateResult:
        """動画ファイルから企画書とSRTファイルを生成

        Args:
            video_path: 動画ファイルのパス
            output_dir: 出力ディレクトリのパス

        Returns:
            処理結果（GenerateResult）
        """
        try:
            self._validate_inputs(video_path, output_dir)

            self._prepare_output_directory(output_dir)

            draft_result = self.draft_generator.generate_from_video(video_path, output_dir)

            draft_file_path = self._generate_draft_file(draft_result, video_path, output_dir)

            subtitle_file_path = self._generate_subtitle_file_delegated(draft_result, video_path, output_dir)

            uploaded_draft_url = None
            uploaded_subtitle_url = None

            if self.upload_enabled and self.google_drive_client and self.upload_folder_id:
                try:
                    print("Google Driveへのアップロードを開始します...")
                    uploaded_draft_url = self.google_drive_client.upload_file(draft_file_path, self.upload_folder_id)
                    uploaded_subtitle_url = self.google_drive_client.upload_file(subtitle_file_path, self.upload_folder_id)
                    print("Google Driveへのアップロードが完了しました")
                except FileUploadError as e:
                    print(f"警告: Google Driveアップロードに失敗しました: {e}")
                except Exception as e:
                    print(f"警告: Google Driveアップロード中に予期しないエラーが発生しました: {e}")

            return GenerateResult(
                draft_file_path=draft_file_path,
                subtitle_file_path=subtitle_file_path,
                success=True,
                uploaded_draft_url=uploaded_draft_url,
                uploaded_subtitle_url=uploaded_subtitle_url,
            )

        except Exception as e:
            return GenerateResult(
                draft_file_path="",
                subtitle_file_path="",
                success=False,
                error_message=str(e),
            )

    def _validate_inputs(self, video_path: str, output_dir: str) -> None:
        """入力パラメータの検証

        Args:
            video_path: 動画ファイルのパス
            output_dir: 出力ディレクトリのパス

        Raises:
            InputValidationError: 入力が無効な場合
        """
        if not video_path or not video_path.strip():
            raise InputValidationError("動画ファイルパスが指定されていません", "video_path")

        if not os.path.exists(video_path):
            raise InputValidationError(f"動画ファイルが存在しません: {video_path}", "video_path")

        if not os.path.isfile(video_path):
            raise InputValidationError(f"指定されたパスはファイルではありません: {video_path}", "video_path")

        if not output_dir or not output_dir.strip():
            raise InputValidationError("出力ディレクトリが指定されていません", "output_dir")

        allowed_extensions = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}
        file_extension = Path(video_path).suffix.lower()
        if file_extension not in allowed_extensions:
            raise InputValidationError(f"サポートされていないファイル形式です: {file_extension}", "video_path")

    def _prepare_output_directory(self, output_dir: str) -> None:
        """出力ディレクトリの準備

        Args:
            output_dir: 出力ディレクトリのパス

        Raises:
            OutputGenerationError: ディレクトリ作成に失敗した場合
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            if not output_path.is_dir():
                raise OutputGenerationError(f"出力ディレクトリの作成に失敗しました: {output_dir}", output_dir)

        except Exception as e:
            raise OutputGenerationError(f"出力ディレクトリの準備に失敗しました: {str(e)}", output_dir)

    def _generate_draft_file(self, draft_result: DraftResult, video_path: str, output_dir: str) -> str:
        """企画書Markdownファイルを生成

        Args:
            draft_result: 企画書生成結果
            video_path: 元の動画ファイルパス
            output_dir: 出力ディレクトリ

        Returns:
            生成されたファイルのパス

        Raises:
            OutputGenerationError: ファイル生成に失敗した場合
        """
        draft_file_path = None
        try:
            video_name = Path(video_path).stem
            draft_file_path = Path(output_dir) / f"{video_name}_draft.md"

            markdown_content = self._build_markdown_content(draft_result, video_path)

            with open(draft_file_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            return str(draft_file_path)

        except Exception as e:
            raise OutputGenerationError(
                f"企画書ファイルの生成に失敗しました: {str(e)}",
                str(draft_file_path) if draft_file_path else None,
            )

    def _generate_subtitle_file_delegated(self, draft_result: DraftResult, video_path: str, output_dir: str) -> str:
        """SRT字幕ファイルの生成をSrtGeneratorに委譲

        Args:
            draft_result: 企画書生成結果
            video_path: 元の動画ファイルパス
            output_dir: 出力ディレクトリ

        Returns:
            生成されたファイルのパス

        Raises:
            OutputGenerationError: ファイル生成に失敗した場合
        """
        subtitle_file_path = None
        try:
            video_name = Path(video_path).stem
            subtitle_file_path = Path(output_dir) / f"{video_name}_subtitle.srt"

            # SrtGeneratorに処理を委譲
            return self.srt_generator.generate_srt_file(draft_result.original_transcription, str(subtitle_file_path))

        except Exception as e:
            raise OutputGenerationError(
                f"字幕ファイルの生成に失敗しました: {str(e)}",
                str(subtitle_file_path) if subtitle_file_path else None,
            )

    def _build_markdown_content(self, draft_result: DraftResult, video_path: str) -> str:
        """企画書のMarkdown内容を構築

        Args:
            draft_result: 企画書生成結果
            video_path: 元の動画ファイルパス

        Returns:
            Markdown形式の企画書内容
        """
        video_name = Path(video_path).name
        content_lines = [
            "# ショート動画企画書",
            "",
            f"**元動画**: {video_name}",
            f"**生成日時**: {self._get_current_datetime()}",
            f"**企画数**: {len(draft_result.proposals)}",
            "",
            "---",
            "",
        ]

        for i, proposal in enumerate(draft_result.proposals, 1):
            content_lines.extend(
                [
                    f"## 企画 {i}: {proposal.title}",
                    "",
                    f"**切り抜き時間**: {self._format_seconds_to_time(proposal.start_time)} - " f"{self._format_seconds_to_time(proposal.end_time)}",
                    f"**尺**: {proposal.end_time - proposal.start_time:.1f}秒",
                    "",
                    "**キャプション**:",
                    f"{proposal.caption}",
                    "",
                    "**キーポイント**:",
                ]
            )

            for point in proposal.key_points:
                content_lines.append(f"- {point}")

            content_lines.extend(
                [
                    "",
                    "---",
                    "",
                ]
            )

        content_lines.extend(
            [
                "## 元の文字起こし",
                "",
                "```",
                draft_result.original_transcription.full_text,
                "```",
            ]
        )

        return "\n".join(content_lines)

    def _format_seconds_to_time(self, seconds: float) -> str:
        """秒数をhh:mm:ss形式に変換

        Args:
            seconds: 変換する秒数

        Returns:
            hh:mm:ss形式の時刻文字列
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _get_current_datetime(self) -> str:
        """現在の日時を文字列で取得

        Returns:
            現在の日時文字列
        """
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def execute_from_drive(self, drive_folder_url: str, output_dir: str) -> GenerateResult:
        """Google Driveフォルダから企画書とSRTファイルを生成

        Args:
            drive_folder_url: Google DriveフォルダのURL
            output_dir: 出力ディレクトリのパス

        Returns:
            処理結果（GenerateResult）
        """
        try:
            self._validate_drive_inputs(drive_folder_url, output_dir)

            self._prepare_output_directory(output_dir)

            video_source = GoogleDriveVideoSource(drive_folder_url, self.google_drive_client)

            video_path = video_source.get_video_path(output_dir)

            draft_result = self.draft_generator.generate_from_video(video_path, output_dir)

            draft_file_path = self._generate_draft_file(draft_result, video_path, output_dir)

            subtitle_file_path = self._generate_subtitle_file_delegated(draft_result, video_path, output_dir)

            video_source.cleanup()

            uploaded_draft_url = None
            uploaded_subtitle_url = None

            if self.upload_enabled and self.google_drive_client and self.upload_folder_id:
                try:
                    print("Google Driveへのアップロードを開始します...")
                    uploaded_draft_url = self.google_drive_client.upload_file(draft_file_path, self.upload_folder_id)
                    uploaded_subtitle_url = self.google_drive_client.upload_file(subtitle_file_path, self.upload_folder_id)
                    print("Google Driveへのアップロードが完了しました")
                except FileUploadError as e:
                    print(f"警告: Google Driveアップロードに失敗しました: {e}")
                except Exception as e:
                    print(f"警告: Google Driveアップロード中に予期しないエラーが発生しました: {e}")

            return GenerateResult(
                draft_file_path=draft_file_path,
                subtitle_file_path=subtitle_file_path,
                success=True,
                uploaded_draft_url=uploaded_draft_url,
                uploaded_subtitle_url=uploaded_subtitle_url,
            )

        except Exception as e:
            return GenerateResult(
                draft_file_path="",
                subtitle_file_path="",
                success=False,
                error_message=str(e),
            )

    def _validate_drive_inputs(self, drive_folder_url: str, output_dir: str) -> None:
        """Google Drive入力パラメータの検証

        Args:
            drive_folder_url: Google DriveフォルダURL
            output_dir: 出力ディレクトリパス

        Raises:
            InputValidationError: 入力が無効な場合
        """
        if not drive_folder_url or not drive_folder_url.strip():
            raise InputValidationError("Google DriveフォルダURLが指定されていません", "drive_folder_url")

        if "drive.google.com/drive/folders/" not in drive_folder_url:
            raise InputValidationError("無効なGoogle DriveフォルダURLです", "drive_folder_url")

        if not output_dir or not output_dir.strip():
            raise InputValidationError("出力ディレクトリが指定されていません", "output_dir")
