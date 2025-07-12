"""文字起こし→企画書ユースケース"""

import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from ..builders.prompt_builder import PromptBuilder
from ..clients.chatgpt_client import ChatGPTClient
from ..models.draft import DraftResult
from ..models.transcription import TranscriptionResult, TranscriptionSegment
from ..models.usecase_results import TranscriptToDraftResult
from ..service.srt_generator import SrtGenerator


class TranscriptToDraftUsecaseError(Exception):
    """TranscriptToDraftUsecase関連のベース例外"""


class TranscriptInputValidationError(TranscriptToDraftUsecaseError):
    """文字起こし入力検証エラー"""

    def __init__(self, message: str, field_name: str | None = None):
        super().__init__(message)
        self.field_name = field_name


class DraftGenerationError(TranscriptToDraftUsecaseError):
    """企画書生成エラー"""

    def __init__(self, message: str, transcript_file: str | None = None):
        super().__init__(message)
        self.transcript_file = transcript_file


class TranscriptToDraftUsecase:
    """文字起こしファイルから企画書と字幕ファイルを生成するユースケース

    責務:
    - transcript.jsonファイルの読み込み・検証
    - ChatGPT APIによる企画書生成
    - 企画書Markdownファイルの出力
    - SRT字幕ファイルの出力
    - エラーハンドリング

    Example:
        >>> usecase = TranscriptToDraftUsecase(chatgpt_client, prompt_builder, srt_generator)
        >>> result = usecase.execute("intermediate/video_transcript.json", "output/")
        >>> if result.success:
        ...     print(f"企画書: {result.draft_file_path}")
        ...     print(f"字幕: {result.subtitle_file_path}")
        企画書: output/video_draft.md
        字幕: output/video_subtitle.srt

    """

    def __init__(self, chatgpt_client: ChatGPTClient, prompt_builder: PromptBuilder, srt_generator: SrtGenerator):
        """TranscriptToDraftUsecaseを初期化

        Args:
            chatgpt_client: ChatGPT APIクライアント
            prompt_builder: プロンプト生成器
            srt_generator: SRT字幕ファイル生成器

        """
        self.chatgpt_client = chatgpt_client
        self.prompt_builder = prompt_builder
        self.srt_generator = srt_generator

    def execute(self, transcript_file_path: str, output_dir: str) -> TranscriptToDraftResult:
        """transcript.jsonから企画書と字幕ファイルを生成

        Args:
            transcript_file_path: 文字起こしJSONファイルのパス
            output_dir: 出力ディレクトリのパス

        Returns:
            処理結果（TranscriptToDraftResult）

        """
        try:
            # 1. 入力検証
            self._validate_input(transcript_file_path, output_dir)

            # 2. 出力ディレクトリ準備
            self._prepare_output_directory(output_dir)

            # 3. transcript.jsonの読み込み
            transcription = self._load_transcript(transcript_file_path)

            # 4. 企画書生成
            draft_result = self._generate_draft(transcription)

            # 5. 企画書ファイル出力
            draft_file_path = self._generate_draft_file(draft_result, transcript_file_path, output_dir)

            # 6. 字幕ファイル出力
            subtitle_file_path = self._generate_subtitle_file(transcription, transcript_file_path, output_dir)

            return TranscriptToDraftResult(success=True, draft_file_path=draft_file_path, subtitle_file_path=subtitle_file_path, transcription=transcription)

        except Exception as e:
            return TranscriptToDraftResult(success=False, draft_file_path="", subtitle_file_path="", error_message=str(e))

    def _validate_input(self, transcript_file_path: str, output_dir: str) -> None:
        """入力パラメータの検証

        Args:
            transcript_file_path: 文字起こしファイルのパス
            output_dir: 出力ディレクトリのパス

        Raises:
            TranscriptInputValidationError: 入力が無効な場合

        """
        if not transcript_file_path or not transcript_file_path.strip():
            raise TranscriptInputValidationError("文字起こしファイルパスが指定されていません", "transcript_file_path")

        if not os.path.exists(transcript_file_path):
            raise TranscriptInputValidationError(f"文字起こしファイルが存在しません: {transcript_file_path}", "transcript_file_path")

        if not os.path.isfile(transcript_file_path):
            raise TranscriptInputValidationError(f"指定されたパスはファイルではありません: {transcript_file_path}", "transcript_file_path")

        if not output_dir or not output_dir.strip():
            raise TranscriptInputValidationError("出力ディレクトリが指定されていません", "output_dir")

    def _prepare_output_directory(self, output_dir: str) -> None:
        """出力ディレクトリの準備

        Args:
            output_dir: 出力ディレクトリのパス

        Raises:
            DraftGenerationError: ディレクトリ作成に失敗した場合

        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            if not output_path.is_dir():
                raise DraftGenerationError(f"出力ディレクトリの作成に失敗しました: {output_dir}")

        except Exception as e:
            raise DraftGenerationError(f"出力ディレクトリの準備に失敗しました: {e!s}") from e

    def _load_transcript(self, transcript_file_path: str) -> TranscriptionResult:
        """transcript.jsonファイルの読み込み

        Args:
            transcript_file_path: 文字起こしファイルのパス

        Returns:
            文字起こし結果

        Raises:
            DraftGenerationError: ファイル読み込みに失敗した場合

        """
        try:
            with open(transcript_file_path, encoding="utf-8") as f:
                data = json.load(f)

            # JSONデータからTranscriptionResultオブジェクトを復元
            return self._deserialize_transcription(data)

        except Exception as e:
            raise DraftGenerationError(f"文字起こしファイルの読み込みに失敗しました: {e!s}", transcript_file_path) from e

    def _deserialize_transcription(self, data: dict) -> TranscriptionResult:
        """辞書からTranscriptionResultオブジェクトを復元

        Args:
            data: デシリアライズする辞書

        Returns:
            復元されたTranscriptionResult

        Raises:
            DraftGenerationError: データ形式が無効な場合

        """
        try:
            segments = [
                TranscriptionSegment(
                    start_time=segment_data["start_time"],
                    end_time=segment_data["end_time"],
                    text=segment_data["text"],
                )
                for segment_data in data["segments"]
            ]

            return TranscriptionResult(segments=segments, full_text=data["full_text"])

        except KeyError as e:
            raise DraftGenerationError(f"文字起こしファイルの形式が無効です。必要なフィールドが見つかりません: {e}") from e
        except Exception as e:
            raise DraftGenerationError(f"文字起こしデータの復元に失敗しました: {e!s}") from e

    def _generate_draft(self, transcription: TranscriptionResult) -> DraftResult:
        """文字起こし結果から企画書を生成

        Args:
            transcription: 文字起こし結果

        Returns:
            企画書生成結果

        Raises:
            DraftGenerationError: 企画書生成に失敗した場合

        """
        try:
            prompt = self.prompt_builder.build_draft_prompt(transcription)
            proposals = self.chatgpt_client.generate_draft(prompt)
            return DraftResult(proposals=proposals, original_transcription=transcription)

        except Exception as e:
            raise DraftGenerationError(f"企画書の生成に失敗しました: {e!s}") from e

    def _generate_draft_file(self, draft_result: DraftResult, transcript_file_path: str, output_dir: str) -> str:
        """企画書Markdownファイルを生成

        Args:
            draft_result: 企画書生成結果
            transcript_file_path: 元の文字起こしファイルパス
            output_dir: 出力ディレクトリ

        Returns:
            生成されたファイルのパス

        Raises:
            DraftGenerationError: ファイル生成に失敗した場合

        """
        try:
            # transcript.jsonのファイル名から元の動画名を推定
            transcript_name = Path(transcript_file_path).stem
            video_name = transcript_name.replace("_transcript", "")

            draft_file_path = Path(output_dir) / f"{video_name}_draft.md"

            # Markdownコンテンツを構築
            markdown_content = self._build_markdown_content(draft_result, video_name)

            with open(draft_file_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            return str(draft_file_path)

        except Exception as e:
            raise DraftGenerationError(f"企画書ファイルの生成に失敗しました: {e!s}") from e

    def _generate_subtitle_file(self, transcription: TranscriptionResult, transcript_file_path: str, output_dir: str) -> str:
        """SRT字幕ファイルを生成

        Args:
            transcription: 文字起こし結果
            transcript_file_path: 元の文字起こしファイルパス
            output_dir: 出力ディレクトリ

        Returns:
            生成されたファイルのパス

        Raises:
            DraftGenerationError: ファイル生成に失敗した場合

        """
        try:
            # transcript.jsonのファイル名から元の動画名を推定
            transcript_name = Path(transcript_file_path).stem
            video_name = transcript_name.replace("_transcript", "")

            subtitle_file_path = Path(output_dir) / f"{video_name}_subtitle.srt"

            # SrtGeneratorに処理を委譲
            return self.srt_generator.generate_srt_file(transcription, str(subtitle_file_path))

        except Exception as e:
            raise DraftGenerationError(f"字幕ファイルの生成に失敗しました: {e!s}") from e

    def _build_markdown_content(self, draft_result: DraftResult, video_name: str) -> str:
        """企画書のMarkdown内容を構築

        Args:
            draft_result: 企画書生成結果
            video_name: 動画名

        Returns:
            Markdown形式の企画書内容

        """
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
                    f"**切り抜き時間**: {self._format_seconds_to_time(proposal.start_time)} - {self._format_seconds_to_time(proposal.end_time)}",
                    f"**尺**: {proposal.end_time - proposal.start_time:.1f}秒",
                    "",
                    "**キャプション**:",
                    f"{proposal.caption}",
                    "",
                    "**キーポイント**:",
                ],
            )

            for point in proposal.key_points:
                content_lines.append(f"- {point}")

            content_lines.extend(
                [
                    "",
                    "---",
                    "",
                ],
            )

        content_lines.extend(
            [
                "## 元の文字起こし",
                "",
                "```",
                draft_result.original_transcription.full_text,
                "```",
            ],
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
        return datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S")
