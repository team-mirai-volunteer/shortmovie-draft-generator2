"""文字起こし→企画書ユースケース（2段階処理版）"""

import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from ..builders.prompt_builder import PromptBuilder
from ..clients.chatgpt_client import ChatGPTClient
from ..models.hooks import DetailedScript, HooksExtractionResult
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


class HooksExtractionError(TranscriptToDraftUsecaseError):
    """フック抽出エラー"""


class ScriptGenerationError(TranscriptToDraftUsecaseError):
    """台本生成エラー"""


class ParallelProcessingError(TranscriptToDraftUsecaseError):
    """並列処理エラー"""


class TranscriptToDraftUsecase:
    """文字起こしファイルから企画書と字幕ファイルを生成するユースケース（2段階処理版）

    責務:
    - transcript.jsonファイルの読み込み・検証
    - 2段階処理（フック抽出→詳細台本作成）の実行
    - 並列処理による詳細台本生成
    - 企画書Markdownファイルの出力
    - SRT字幕ファイルの出力
    - エラーハンドリング

    Example:
        >>> usecase = TranscriptToDraftUsecase(chatgpt_client, prompt_builder, srt_generator)
        >>> result = usecase.execute("intermediate/文字起こし_video.json", "output/")
        >>> if result.success:
        ...     print(f"詳細台本: {result.draft_file_path}")
        ...     print(f"字幕: {result.subtitle_file_path}")
        詳細台本: output/企画案_video.md
        字幕: output/字幕_video.srt

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
        """2段階処理による企画書と字幕ファイルの生成

        Args:
            transcript_file_path: 文字起こしJSONファイルのパス
            output_dir: 出力ディレクトリのパス

        Returns:
            処理結果（TranscriptToDraftResult）

        """
        try:
            # 1. 既存の前処理（入力検証、transcript読み込み）
            self._validate_input(transcript_file_path, output_dir)
            self._prepare_output_directory(output_dir)
            transcription = self._load_transcript(transcript_file_path)

            # 2. フェーズ1: フック抽出
            hooks_result = self._extract_hooks_phase(transcription)

            # 3. フェーズ2: 詳細台本作成（並列）
            detailed_scripts = self._generate_scripts_phase(hooks_result)

            # 4. 結果統合・ファイル出力
            return self._generate_output_files(hooks_result, detailed_scripts, transcript_file_path, output_dir)

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

    def _extract_hooks_phase(self, transcription: TranscriptionResult) -> HooksExtractionResult:
        """フェーズ1: フック抽出

        Args:
            transcription: 文字起こし結果

        Returns:
            フック抽出結果

        Raises:
            HooksExtractionError: フック抽出に失敗した場合

        """
        try:
            # フック抽出用プロンプトを構築
            hooks_prompt = self.prompt_builder.build_hooks_prompt(transcription)

            # ChatGPT APIでフック抽出
            hook_items = self.chatgpt_client.extract_hooks(hooks_prompt)

            return HooksExtractionResult(items=hook_items, original_transcription=transcription)

        except Exception as e:
            raise HooksExtractionError(f"フック抽出に失敗しました: {e}") from e

    def _generate_scripts_phase(self, hooks_result: HooksExtractionResult) -> list[DetailedScript]:
        """フェーズ2: 詳細台本作成（並列）

        Args:
            hooks_result: フック抽出結果

        Returns:
            詳細台本のリスト

        Raises:
            ScriptGenerationError: 台本生成に失敗した場合

        """
        try:
            # 並列で詳細台本を生成
            detailed_scripts = self.chatgpt_client.generate_detailed_scripts_parallel(
                hooks_result.items, hooks_result.original_transcription.segments, self.prompt_builder
            )

            if not detailed_scripts:
                raise ScriptGenerationError("全ての台本生成に失敗しました")

            return detailed_scripts

        except Exception as e:
            raise ScriptGenerationError(f"詳細台本生成に失敗しました: {e}") from e

    def _generate_output_files(
        self, hooks_result: HooksExtractionResult, detailed_scripts: list[DetailedScript], transcript_file_path: str, output_dir: str
    ) -> TranscriptToDraftResult:
        """結果統合とファイル出力

        Args:
            hooks_result: フック抽出結果
            detailed_scripts: 詳細台本のリスト
            transcript_file_path: 元の文字起こしファイルパス
            output_dir: 出力ディレクトリ

        Returns:
            処理結果

        """
        try:
            # ファイル名のベースを取得
            transcript_name = Path(transcript_file_path).stem
            video_name = transcript_name.replace("_transcript", "")

            # 1. フック抽出結果をJSONで保存
            self._save_hooks_result(hooks_result, video_name, output_dir)

            # 2. 詳細台本をMarkdownで保存
            scripts_file_path = self._save_detailed_scripts(detailed_scripts, video_name, output_dir)

            # 3. 字幕ファイル生成（既存処理）
            subtitle_file_path = self._generate_subtitle_file(hooks_result.original_transcription, transcript_file_path, output_dir)

            return TranscriptToDraftResult(
                success=True,
                draft_file_path=scripts_file_path,
                subtitle_file_path=subtitle_file_path,
                transcription=hooks_result.original_transcription,
            )

        except Exception as e:
            raise DraftGenerationError(f"出力ファイル生成に失敗しました: {e!s}") from e

    def _save_hooks_result(self, hooks_result: HooksExtractionResult, video_name: str, output_dir: str) -> str:
        """フック抽出結果をJSONファイルに保存"""
        hooks_file_path = Path(output_dir) / f"{video_name}_hooks.json"

        hooks_data = {
            "extraction_timestamp": self._get_current_datetime(),
            "original_video": video_name,
            "items": [
                {
                    "first_hook": item.first_hook,
                    "second_hook": item.second_hook,
                    "third_hook": item.third_hook,
                    "summary": item.summary,
                }
                for item in hooks_result.items
            ],
        }

        with open(hooks_file_path, "w", encoding="utf-8") as f:
            json.dump(hooks_data, f, ensure_ascii=False, indent=2)

        return str(hooks_file_path)

    def _save_detailed_scripts(self, detailed_scripts: list[DetailedScript], video_name: str, output_dir: str) -> str:
        """詳細台本をMarkdownファイルに保存"""
        scripts_file_path = Path(output_dir) / f"企画案_{video_name}.md"

        content_lines = [
            "# 詳細台本集",
            "",
            f"**元動画**: {video_name}",
            f"**生成日時**: {self._get_current_datetime()}",
            f"**台本数**: {len(detailed_scripts)}",
            "",
            "---",
            "",
        ]

        for i, script in enumerate(detailed_scripts, 1):
            content_lines.extend(
                [
                    f"## フック{i}: {script.hook_item.summary}",
                    "",
                    f"**想定時間**: {script.duration_seconds}秒",
                    "",
                    "### フック詳細",
                    f"- **First Hook**: {script.hook_item.first_hook}",
                    f"- **Second Hook**: {script.hook_item.second_hook}",
                    f"- **Third Hook**: {script.hook_item.third_hook}",
                    "",
                    "### 台本内容",
                    script.script_content,
                    "",
                    "---",
                    "",
                ]
            )

        content = "\n".join(content_lines)

        with open(scripts_file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(scripts_file_path)

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
            video_name = transcript_name.replace("文字起こし_", "")

            subtitle_file_path = Path(output_dir) / f"字幕_{video_name}.srt"

            # SrtGeneratorに処理を委譲
            return self.srt_generator.generate_srt_file(transcription, str(subtitle_file_path))

        except Exception as e:
            raise DraftGenerationError(f"字幕ファイルの生成に失敗しました: {e!s}") from e

    def _get_current_datetime(self) -> str:
        """現在の日時を文字列で取得

        Returns:
            現在の日時文字列

        """
        return datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S")
