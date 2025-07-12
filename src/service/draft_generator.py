"""企画書生成サービス"""

import json
import os
from pathlib import Path

from ..builders.prompt_builder import PromptBuilder
from ..clients.chatgpt_client import ChatGPTClient
from ..clients.whisper_client import WhisperClient
from ..models.draft import DraftResult, ShortVideoProposal
from ..models.transcription import TranscriptionResult, TranscriptionSegment


class DraftGeneratorError(Exception):
    """DraftGenerator関連のベース例外"""


class TranscriptionError(DraftGeneratorError):
    """文字起こし処理エラー"""

    def __init__(self, message: str, video_path: str):
        super().__init__(message)
        self.video_path = video_path


class DraftGenerationError(DraftGeneratorError):
    """企画書生成エラー"""

    def __init__(self, message: str, transcription_file: str | None = None):
        super().__init__(message)
        self.transcription_file = transcription_file


class DraftGenerator:
    """企画書生成サービス

    動画ファイルから文字起こしを行い、ChatGPTを使用してショート動画企画書を生成します。
    中間データ（文字起こし結果）の保存・管理機能も提供します。

    Example:
        >>> generator = DraftGenerator(whisper_client, chatgpt_client, prompt_builder)
        >>> transcription = generator.transcribe_video("input/video.mp4", "output/")
        >>> draft = generator.generate_draft(transcription)
        >>> print(f"企画数: {len(draft.proposals)}")
        企画数: 5

    """

    def __init__(
        self,
        whisper_client: WhisperClient,
        chatgpt_client: ChatGPTClient,
        prompt_builder: PromptBuilder,
    ):
        """DraftGeneratorを初期化

        Args:
            whisper_client: Whisper APIクライアント
            chatgpt_client: ChatGPT APIクライアント
            prompt_builder: プロンプト生成器

        """
        self.whisper_client = whisper_client
        self.chatgpt_client = chatgpt_client
        self.prompt_builder = prompt_builder

    def transcribe_video(self, video_path: str, output_dir: str) -> TranscriptionResult:
        """動画ファイルから文字起こしを実行し、結果を保存

        Args:
            video_path: 動画ファイルのパス
            output_dir: 出力ディレクトリ

        Returns:
            文字起こし結果

        Raises:
            TranscriptionError: 文字起こし処理に失敗した場合

        """
        try:
            transcription = self.whisper_client.transcribe(video_path)

            self._save_transcription(transcription, video_path, output_dir)

            return transcription

        except Exception as e:
            raise TranscriptionError(f"動画の文字起こしに失敗しました: {e!s}", video_path) from e

    def generate_draft(self, transcription: TranscriptionResult) -> DraftResult:
        """文字起こし結果から企画書を生成

        Args:
            transcription: 文字起こし結果

        Returns:
            企画書生成結果

        Raises:
            DraftGenerationError: 企画書生成に失敗した場合

        """
        try:
            # 2段階処理を使用
            # 1. フック抽出
            hooks_prompt = self.prompt_builder.build_hooks_prompt(transcription)
            hook_items = self.chatgpt_client.extract_hooks(hooks_prompt)

            # 2. 詳細台本生成（並列処理）
            detailed_scripts = self.chatgpt_client.generate_detailed_scripts_parallel(
                hook_items, transcription.segments, self.prompt_builder
            )

            # 従来のDraftResult形式に変換（後方互換性のため）
            proposals = []
            for script in detailed_scripts:
                # DetailedScriptをShortVideoProposalに変換
                # セグメントから開始・終了時刻を推定（最初と最後のセグメント）
                start_time = script.segments_used[0].start_time if script.segments_used else 0.0
                end_time = script.segments_used[-1].end_time if script.segments_used else script.duration_seconds

                proposal = ShortVideoProposal(
                    title=script.hook_item.first_hook,
                    start_time=start_time,
                    end_time=end_time,
                    caption=script.hook_item.summary,
                    key_points=[
                        script.hook_item.first_hook,
                        script.hook_item.second_hook,
                        script.hook_item.third_hook,
                        script.hook_item.last_conclusion
                    ]
                )
                proposals.append(proposal)

            return DraftResult(proposals=proposals, original_transcription=transcription)

        except Exception as e:
            raise DraftGenerationError(f"企画書の生成に失敗しました: {e!s}") from e

    def generate_from_video(self, video_path: str, output_dir: str) -> DraftResult:
        """動画ファイルから直接企画書を生成（文字起こし→企画書生成の一連の処理）

        Args:
            video_path: 動画ファイルのパス
            output_dir: 出力ディレクトリ

        Returns:
            企画書生成結果

        Raises:
            TranscriptionError: 文字起こし処理に失敗した場合
            DraftGenerationError: 企画書生成に失敗した場合

        """
        transcription = self.transcribe_video(video_path, output_dir)
        return self.generate_draft(transcription)

    def load_transcription(self, transcription_file: str) -> TranscriptionResult:
        """保存された文字起こし結果を読み込み

        Args:
            transcription_file: 文字起こしファイルのパス

        Returns:
            文字起こし結果

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            DraftGenerationError: ファイル読み込みに失敗した場合

        """
        if not os.path.exists(transcription_file):
            raise FileNotFoundError(f"文字起こしファイルが見つかりません: {transcription_file}")

        try:
            with open(transcription_file, encoding="utf-8") as f:
                data = json.load(f)

            return self._deserialize_transcription(data)

        except Exception as e:
            raise DraftGenerationError(
                f"文字起こしファイルの読み込みに失敗しました: {e!s}",
                transcription_file,
            ) from e

    def _save_transcription(self, transcription: TranscriptionResult, video_path: str, output_dir: str) -> str:
        """文字起こし結果をJSONファイルに保存

        Args:
            transcription: 保存する文字起こし結果
            video_path: 元の動画ファイルパス
            output_dir: 出力ディレクトリ

        Returns:
            保存されたファイルのパス

        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        video_name = Path(video_path).stem
        transcription_file = output_path / f"{video_name}_transcription.json"

        data = self._serialize_transcription(transcription)

        with open(transcription_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return str(transcription_file)

    def _serialize_transcription(self, transcription: TranscriptionResult) -> dict:
        """TranscriptionResultをシリアライズ可能な辞書に変換

        Args:
            transcription: シリアライズする文字起こし結果

        Returns:
            シリアライズされた辞書

        """
        return {
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

    def _deserialize_transcription(self, data: dict) -> TranscriptionResult:
        """辞書からTranscriptionResultオブジェクトを復元

        Args:
            data: デシリアライズする辞書

        Returns:
            復元されたTranscriptionResult

        """
        segments = [
            TranscriptionSegment(
                start_time=segment_data["start_time"],
                end_time=segment_data["end_time"],
                text=segment_data["text"],
            )
            for segment_data in data["segments"]
        ]

        return TranscriptionResult(segments=segments, full_text=data["full_text"])
