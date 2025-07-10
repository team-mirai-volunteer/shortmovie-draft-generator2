"""GenerateShortDraftUsecaseのテスト"""

import pytest
from unittest.mock import Mock, patch, mock_open

from src.usecases.generate_short_draft_usecase import (
    GenerateShortDraftUsecase,
    InputValidationError,
)
from src.service.srt_generator import SrtGenerator
from src.models.result import GenerateResult
from src.models.draft import DraftResult, ShortVideoProposal
from src.models.transcription import TranscriptionResult, TranscriptionSegment


class TestGenerateShortDraftUsecase:
    """GenerateShortDraftUsecaseのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化"""
        self.mock_draft_generator = Mock()
        self.mock_srt_generator = Mock()
        self.usecase = GenerateShortDraftUsecase(
            self.mock_draft_generator, self.mock_srt_generator
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

        self.sample_draft_result = DraftResult(
            proposals=self.sample_proposals,
            original_transcription=self.sample_transcription,
        )

    def test_init(self):
        """初期化のテスト"""
        assert self.usecase.draft_generator == self.mock_draft_generator
        assert self.usecase.srt_generator == self.mock_srt_generator

    def test_validate_inputs_empty_video_path(self):
        """空の動画パスの検証エラーテスト"""
        with pytest.raises(
            InputValidationError, match="動画ファイルパスが指定されていません"
        ):
            self.usecase._validate_inputs("", "output/")

    @patch("os.path.exists")
    def test_validate_inputs_nonexistent_video(self, mock_exists):
        """存在しない動画ファイルの検証エラーテスト"""
        mock_exists.return_value = False
        with pytest.raises(InputValidationError, match="動画ファイルが存在しません"):
            self.usecase._validate_inputs("nonexistent.mp4", "output/")

    @patch("os.path.exists")
    @patch("os.path.isfile")
    def test_validate_inputs_not_file(self, mock_isfile, mock_exists):
        """ファイルでないパスの検証エラーテスト"""
        mock_exists.return_value = True
        mock_isfile.return_value = False
        with pytest.raises(
            InputValidationError, match="指定されたパスはファイルではありません"
        ):
            self.usecase._validate_inputs("directory/", "output/")

    @patch("os.path.exists")
    @patch("os.path.isfile")
    def test_validate_inputs_empty_output_dir(self, mock_isfile, mock_exists):
        """空の出力ディレクトリの検証エラーテスト"""
        mock_exists.return_value = True
        mock_isfile.return_value = True
        with pytest.raises(
            InputValidationError, match="出力ディレクトリが指定されていません"
        ):
            self.usecase._validate_inputs("video.mp4", "")

    @patch("os.path.exists")
    @patch("os.path.isfile")
    def test_validate_inputs_unsupported_format(self, mock_isfile, mock_exists):
        """サポートされていないファイル形式の検証エラーテスト"""
        mock_exists.return_value = True
        mock_isfile.return_value = True
        with pytest.raises(
            InputValidationError, match="サポートされていないファイル形式です"
        ):
            self.usecase._validate_inputs("video.txt", "output/")

    @patch("os.path.exists")
    @patch("os.path.isfile")
    def test_validate_inputs_success(self, mock_isfile, mock_exists):
        """正常な入力検証のテスト"""
        mock_exists.return_value = True
        mock_isfile.return_value = True
        self.usecase._validate_inputs("video.mp4", "output/")

    @patch("src.usecases.generate_short_draft_usecase.Path")
    def test_prepare_output_directory_success(self, mock_path):
        """正常な出力ディレクトリ準備のテスト"""
        mock_path_instance = Mock()
        mock_path_instance.mkdir = Mock()
        mock_path_instance.is_dir.return_value = True
        mock_path.return_value = mock_path_instance

        self.usecase._prepare_output_directory("output/")
        mock_path_instance.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_format_seconds_to_time(self):
        """秒数から時刻形式への変換テスト"""
        assert self.usecase._format_seconds_to_time(3661.0) == "01:01:01"
        assert self.usecase._format_seconds_to_time(90.0) == "00:01:30"
        assert self.usecase._format_seconds_to_time(30.0) == "00:00:30"

    def test_build_markdown_content(self):
        """Markdown内容構築のテスト"""
        content = self.usecase._build_markdown_content(
            self.sample_draft_result, "test_video.mp4"
        )

        assert "# ショート動画企画書" in content
        assert "**元動画**: test_video.mp4" in content
        assert "## 企画 1: テストタイトル" in content
        assert "**切り抜き時間**: 00:00:00 - 00:00:10" in content
        assert "**キャプション**:" in content
        assert "テストキャプション" in content
        assert "- ポイント1" in content
        assert "- ポイント2" in content
        assert "## 元の文字起こし" in content

    @patch("os.path.exists")
    @patch("os.path.isfile")
    @patch("src.usecases.generate_short_draft_usecase.Path")
    @patch("builtins.open", new_callable=mock_open)
    def test_execute_success(self, mock_file, mock_path, mock_isfile, mock_exists):
        """正常な実行のテスト"""
        mock_exists.return_value = True
        mock_isfile.return_value = True

        mock_video_path = Mock()
        mock_video_path.stem = "test_video"
        mock_video_path.suffix.lower.return_value = ".mp4"

        mock_output_path = Mock()
        mock_output_path.mkdir = Mock()
        mock_output_path.is_dir.return_value = True

        mock_draft_file_path = Mock()
        mock_draft_file_path.__str__ = Mock(return_value="output/test_video_draft.md")

        mock_subtitle_file_path = Mock()
        mock_subtitle_file_path.__str__ = Mock(
            return_value="output/test_video_subtitle.srt"
        )

        def path_side_effect(path_str):
            if path_str == "test_video.mp4":
                return mock_video_path
            elif path_str == "output/":
                return mock_output_path
            else:
                return Mock()

        mock_path.side_effect = path_side_effect

        mock_output_path.__truediv__ = Mock()
        mock_output_path.__truediv__.side_effect = lambda x: (
            mock_draft_file_path if "draft" in x else mock_subtitle_file_path
        )

        self.mock_draft_generator.generate_from_video.return_value = (
            self.sample_draft_result
        )
        self.mock_srt_generator.generate_srt_file.return_value = (
            "output/test_video_subtitle.srt"
        )

        result = self.usecase.execute("test_video.mp4", "output/")

        assert isinstance(result, GenerateResult)
        assert result.success is True
        assert result.error_message is None
        assert "test_video_draft.md" in result.draft_file_path
        assert "test_video_subtitle.srt" in result.subtitle_file_path

        self.mock_draft_generator.generate_from_video.assert_called_once_with(
            "test_video.mp4", "output/"
        )

        # SrtGeneratorのメソッド呼び出しを検証
        self.mock_srt_generator.generate_srt_file.assert_called_once()
        # 第1引数がTranscriptionResultであることを確認
        assert (
            self.mock_srt_generator.generate_srt_file.call_args[0][0]
            == self.sample_transcription
        )

    @patch("os.path.exists")
    @patch("os.path.isfile")
    @patch("src.usecases.generate_short_draft_usecase.Path")
    def test_execute_error_handling(self, mock_path, mock_isfile, mock_exists):
        """エラーハンドリングのテスト"""
        mock_exists.return_value = True
        mock_isfile.return_value = True

        mock_path_instance = Mock()
        mock_path_instance.mkdir = Mock()
        mock_path_instance.is_dir.return_value = True
        mock_path_instance.suffix.lower.return_value = ".mp4"
        mock_path.return_value = mock_path_instance

        self.mock_draft_generator.generate_from_video.side_effect = Exception(
            "Test error"
        )

        result = self.usecase.execute("test_video.mp4", "output/")

        assert isinstance(result, GenerateResult)
        assert result.success is False
        assert "Test error" in result.error_message
        assert result.draft_file_path == ""
        assert result.subtitle_file_path == ""


@pytest.mark.integration
class TestGenerateShortDraftUsecaseIntegration:
    """GenerateShortDraftUsecaseの統合テスト"""

    def test_full_workflow_integration(self):
        """完全なワークフローの統合テスト"""
        import os
        import tempfile

        if not os.getenv("INTEGRATION_TEST"):
            pytest.skip("統合テストはINTEGRATION_TEST=trueの場合のみ実行")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEYが設定されていません")

        from src.clients.whisper_client import WhisperClient
        from src.clients.chatgpt_client import ChatGPTClient
        from src.builders.prompt_builder import PromptBuilder
        from src.service.draft_generator import DraftGenerator

        whisper_client = WhisperClient(api_key)
        chatgpt_client = ChatGPTClient(api_key)
        prompt_builder = PromptBuilder()
        draft_generator = DraftGenerator(whisper_client, chatgpt_client, prompt_builder)

        # SrtGeneratorのインスタンスを作成
        srt_generator = SrtGenerator()

        usecase = GenerateShortDraftUsecase(draft_generator, srt_generator)

        with tempfile.TemporaryDirectory() as temp_dir:
            sample_transcription = TranscriptionResult(
                segments=[
                    TranscriptionSegment(
                        0.0, 5.0, "こんにちは、今日はショート動画について話します"
                    ),
                    TranscriptionSegment(5.0, 10.0, "最初に重要なのは冒頭の2秒です"),
                ],
                full_text="こんにちは、今日はショート動画について話します。最初に重要なのは冒頭の2秒です。",
            )

            sample_proposals = [
                ShortVideoProposal(
                    title="ショート動画作成のコツ",
                    start_time=0.0,
                    end_time=10.0,
                    caption="ショート動画作成の基本を学ぼう！ #ショート動画 #YouTube",
                    key_points=["冒頭2秒が重要", "視聴者の興味を引く", "簡潔な内容"],
                )
            ]

            draft_result = DraftResult(
                proposals=sample_proposals,
                original_transcription=sample_transcription,
            )

            with patch.object(
                draft_generator, "generate_from_video", return_value=draft_result
            ):
                result = usecase.execute("dummy_video.mp4", temp_dir)

                assert result.success is True
                assert os.path.exists(result.draft_file_path)
                assert os.path.exists(result.subtitle_file_path)

                with open(result.draft_file_path, "r", encoding="utf-8") as f:
                    draft_content = f.read()
                    assert "# ショート動画企画書" in draft_content
                    assert "ショート動画作成のコツ" in draft_content

                with open(result.subtitle_file_path, "r", encoding="utf-8") as f:
                    subtitle_content = f.read()
                    assert "00:00:00,000 --> 00:00:05,000" in subtitle_content
                    assert (
                        "こんにちは、今日はショート動画について話します"
                        in subtitle_content
                    )
