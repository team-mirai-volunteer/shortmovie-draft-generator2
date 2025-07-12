"""DraftGeneratorのテスト"""

import pytest
from unittest.mock import Mock, patch, mock_open

from src.service.draft_generator import (
    DraftGenerator,
    TranscriptionError,
    DraftGenerationError,
)
from src.models.transcription import TranscriptionResult, TranscriptionSegment
from src.models.draft import DraftResult, ShortVideoProposal


class TestDraftGenerator:
    """DraftGeneratorのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化"""
        self.mock_whisper_client = Mock()
        self.mock_chatgpt_client = Mock()
        self.mock_prompt_builder = Mock()

        self.generator = DraftGenerator(
            whisper_client=self.mock_whisper_client,
            chatgpt_client=self.mock_chatgpt_client,
            prompt_builder=self.mock_prompt_builder,
        )

        self.sample_transcription = TranscriptionResult(
            segments=[
                TranscriptionSegment(0.0, 5.0, "こんにちは"),
                TranscriptionSegment(5.0, 10.0, "今日は良い天気ですね"),
            ],
            full_text="こんにちは今日は良い天気ですね",
        )

        self.sample_proposals = [
            ShortVideoProposal(
                title="テストタイトル",
                start_time=0.0,
                end_time=10.0,
                caption="テストキャプション",
                key_points=["ポイント1", "ポイント2"],
            )
        ]

    def test_init(self):
        """初期化のテスト"""
        assert self.generator.whisper_client == self.mock_whisper_client
        assert self.generator.chatgpt_client == self.mock_chatgpt_client
        assert self.generator.prompt_builder == self.mock_prompt_builder

    @patch("src.service.draft_generator.Path")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_transcribe_video_success(self, mock_json_dump, mock_file, mock_path):
        """正常な動画文字起こしのテスト"""
        mock_path.return_value.mkdir = Mock()
        mock_path.return_value.stem = "test_video"

        self.mock_whisper_client.transcribe.return_value = self.sample_transcription

        result = self.generator.transcribe_video("test_video.mp4", "output/")

        assert result == self.sample_transcription
        self.mock_whisper_client.transcribe.assert_called_once_with("test_video.mp4")
        mock_json_dump.assert_called_once()

    def test_transcribe_video_error(self):
        """動画文字起こしエラーのテスト"""
        self.mock_whisper_client.transcribe.side_effect = Exception("API Error")

        with pytest.raises(TranscriptionError, match="動画の文字起こしに失敗しました"):
            self.generator.transcribe_video("test_video.mp4", "output/")

    def test_generate_draft_success(self):
        """正常な企画書生成のテスト"""
        self.mock_prompt_builder.build_draft_prompt.return_value = "test prompt"
        self.mock_chatgpt_client.generate_draft.return_value = self.sample_proposals

        result = self.generator.generate_draft(self.sample_transcription)

        assert isinstance(result, DraftResult)
        assert result.proposals == self.sample_proposals
        assert result.original_transcription == self.sample_transcription

        self.mock_prompt_builder.build_draft_prompt.assert_called_once_with(self.sample_transcription)
        self.mock_chatgpt_client.generate_draft.assert_called_once_with("test prompt")

    def test_generate_draft_error(self):
        """企画書生成エラーのテスト"""
        self.mock_prompt_builder.build_draft_prompt.side_effect = Exception("Prompt Error")

        with pytest.raises(DraftGenerationError, match="企画書の生成に失敗しました"):
            self.generator.generate_draft(self.sample_transcription)

    @patch("src.service.draft_generator.Path")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_generate_from_video_success(self, mock_json_dump, mock_file, mock_path):
        """動画から直接企画書生成の成功テスト"""
        mock_path.return_value.mkdir = Mock()
        mock_path.return_value.stem = "test_video"

        self.mock_whisper_client.transcribe.return_value = self.sample_transcription
        self.mock_prompt_builder.build_draft_prompt.return_value = "test prompt"
        self.mock_chatgpt_client.generate_draft.return_value = self.sample_proposals

        result = self.generator.generate_from_video("test_video.mp4", "output/")

        assert isinstance(result, DraftResult)
        assert result.proposals == self.sample_proposals
        assert result.original_transcription == self.sample_transcription

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    def test_load_transcription_success(self, mock_json_load, mock_file, mock_exists):
        """文字起こし結果読み込み成功のテスト"""
        mock_exists.return_value = True
        mock_json_load.return_value = {
            "full_text": "こんにちは今日は良い天気ですね",
            "segments": [
                {"start_time": 0.0, "end_time": 5.0, "text": "こんにちは"},
                {"start_time": 5.0, "end_time": 10.0, "text": "今日は良い天気ですね"},
            ],
        }

        result = self.generator.load_transcription("文字起こし_test.json")

        assert isinstance(result, TranscriptionResult)
        assert result.full_text == "こんにちは今日は良い天気ですね"
        assert len(result.segments) == 2
        assert result.segments[0].text == "こんにちは"

    @patch("os.path.exists")
    def test_load_transcription_file_not_found(self, mock_exists):
        """文字起こし結果読み込みファイル未存在のテスト"""
        mock_exists.return_value = False

        with pytest.raises(FileNotFoundError, match="文字起こしファイルが見つかりません"):
            self.generator.load_transcription("nonexistent.json")

    def test_serialize_transcription(self):
        """文字起こし結果シリアライズのテスト"""
        result = self.generator._serialize_transcription(self.sample_transcription)

        expected = {
            "full_text": "こんにちは今日は良い天気ですね",
            "segments": [
                {"start_time": 0.0, "end_time": 5.0, "text": "こんにちは"},
                {"start_time": 5.0, "end_time": 10.0, "text": "今日は良い天気ですね"},
            ],
        }

        assert result == expected

    def test_deserialize_transcription(self):
        """文字起こし結果デシリアライズのテスト"""
        data = {
            "full_text": "こんにちは今日は良い天気ですね",
            "segments": [
                {"start_time": 0.0, "end_time": 5.0, "text": "こんにちは"},
                {"start_time": 5.0, "end_time": 10.0, "text": "今日は良い天気ですね"},
            ],
        }

        result = self.generator._deserialize_transcription(data)

        assert isinstance(result, TranscriptionResult)
        assert result.full_text == "こんにちは今日は良い天気ですね"
        assert len(result.segments) == 2
        assert result.segments[0].text == "こんにちは"
        assert result.segments[1].text == "今日は良い天気ですね"


@pytest.mark.integration
class TestDraftGeneratorIntegration:
    """DraftGeneratorの統合テスト"""

    def test_full_workflow_integration(self):
        """完全なワークフローの統合テスト"""
        import os

        if not os.getenv("INTEGRATION_TEST"):
            pytest.skip("統合テストはINTEGRATION_TEST=trueの場合のみ実行")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEYが設定されていません")

        from src.clients.whisper_client import WhisperClient
        from src.clients.chatgpt_client import ChatGPTClient
        from src.builders.prompt_builder import PromptBuilder

        whisper_client = WhisperClient(api_key)
        chatgpt_client = ChatGPTClient(api_key)
        prompt_builder = PromptBuilder()

        generator = DraftGenerator(whisper_client, chatgpt_client, prompt_builder)

        sample_transcription = TranscriptionResult(
            segments=[
                TranscriptionSegment(0.0, 5.0, "こんにちは、今日はショート動画について話します"),
                TranscriptionSegment(5.0, 10.0, "最初に重要なのは冒頭の2秒です"),
            ],
            full_text="こんにちは、今日はショート動画について話します。最初に重要なのは冒頭の2秒です。",
        )

        result = generator.generate_draft(sample_transcription)

        assert isinstance(result, DraftResult)
        assert len(result.proposals) > 0
        assert result.original_transcription == sample_transcription

        for proposal in result.proposals:
            assert isinstance(proposal, ShortVideoProposal)
            assert proposal.title
            assert proposal.caption
            assert len(proposal.key_points) > 0
