"""SrtGeneratorのテスト"""

import os  # noqa: F401
import pytest
from unittest.mock import patch, mock_open

from src.service.srt_generator import SrtGenerator, SrtGenerationError
from src.models.transcription import TranscriptionResult, TranscriptionSegment


class TestSrtGenerator:
    """SrtGeneratorのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化"""
        self.generator = SrtGenerator()

        self.sample_transcription = TranscriptionResult(
            segments=[
                TranscriptionSegment(0.0, 5.0, "こんにちは"),
                TranscriptionSegment(5.0, 10.0, "今日は良い天気ですね"),
            ],
            full_text="こんにちは今日は良い天気ですね",
        )

    def test_init(self):
        """初期化のテスト"""
        assert isinstance(self.generator, SrtGenerator)

    def test_format_seconds_to_srt_time(self):
        """秒数からSRT時刻形式への変換テスト"""
        assert self.generator.format_seconds_to_srt_time(3661.5) == "01:01:01,500"
        assert self.generator.format_seconds_to_srt_time(90.123) == "00:01:30,123"
        assert self.generator.format_seconds_to_srt_time(30.0) == "00:00:30,000"

    def test_build_srt_content(self):
        """SRT内容構築のテスト"""
        content = self.generator.build_srt_content(self.sample_transcription)

        expected_lines = [
            "1",
            "00:00:00,000 --> 00:00:05,000",
            "こんにちは",
            "",
            "2",
            "00:00:05,000 --> 00:00:10,000",
            "今日は良い天気ですね",
            "",
        ]

        assert content == "\n".join(expected_lines)

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("os.path.dirname")
    def test_generate_srt_file_success(
        self, mock_dirname, mock_exists, mock_makedirs, mock_file
    ):
        """SRTファイル生成成功のテスト"""
        mock_dirname.return_value = "output"
        mock_exists.return_value = True

        result = self.generator.generate_srt_file(
            self.sample_transcription, "output/subtitle.srt"
        )

        assert result == "output/subtitle.srt"
        mock_file.assert_called_once_with("output/subtitle.srt", "w", encoding="utf-8")
        mock_file().write.assert_called_once()
        # 書き込まれた内容を検証
        written_content = mock_file().write.call_args[0][0]
        assert "00:00:00,000 --> 00:00:05,000" in written_content
        assert "こんにちは" in written_content

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("os.path.dirname")
    def test_generate_srt_file_create_directory(
        self, mock_dirname, mock_exists, mock_makedirs, mock_file
    ):
        """出力ディレクトリが存在しない場合のテスト"""
        mock_dirname.return_value = "output"
        mock_exists.return_value = False

        result = self.generator.generate_srt_file(
            self.sample_transcription, "output/subtitle.srt"
        )

        assert result == "output/subtitle.srt"
        mock_makedirs.assert_called_once_with("output", exist_ok=True)
        mock_file.assert_called_once_with("output/subtitle.srt", "w", encoding="utf-8")

    @patch("builtins.open")
    def test_generate_srt_file_error(self, mock_open):
        """ファイル生成エラーのテスト"""
        mock_open.side_effect = IOError("テストエラー")

        with pytest.raises(SrtGenerationError) as excinfo:
            self.generator.generate_srt_file(
                self.sample_transcription, "output/subtitle.srt"
            )

        assert "字幕ファイルの生成に失敗しました" in str(excinfo.value)
        assert "テストエラー" in str(excinfo.value)
        assert excinfo.value.file_path == "output/subtitle.srt"
