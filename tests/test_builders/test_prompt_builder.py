"""PromptBuilderのテストモジュール"""

import pytest

from src.builders.prompt_builder import PromptBuilder
from src.models.transcription import TranscriptionResult, TranscriptionSegment


class TestPromptBuilder:
    """PromptBuilderの基本機能テスト"""

    def test_instance_creation(self):
        """インスタンス生成テスト"""
        builder = PromptBuilder()
        assert builder is not None

    def test_build_draft_prompt_basic(self):
        """基本的なプロンプト生成テスト"""
        segments = [TranscriptionSegment(0.0, 10.0, "テスト内容")]
        transcription = TranscriptionResult(segments, "テスト内容")
        builder = PromptBuilder()

        prompt = builder.build_draft_prompt(transcription)

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "テスト内容" in prompt
        assert "json形式" in prompt
        assert "first_impact" in prompt

    def test_prompt_contains_best_practices(self):
        """プロンプトにベストプラクティスが含まれているかテスト"""
        segments = [TranscriptionSegment(0.0, 10.0, "テスト")]
        transcription = TranscriptionResult(segments, "テスト")
        builder = PromptBuilder()

        prompt = builder.build_draft_prompt(transcription)

        assert "冒頭2秒でインパクト" in prompt
        assert "視聴時間をハック" in prompt
        assert "最初の接点" in prompt

    def test_build_draft_prompt_with_empty_segments_raises_error(self):
        """空のセグメントでエラーが発生することをテスト"""
        transcription = TranscriptionResult([], "テスト内容")
        builder = PromptBuilder()

        with pytest.raises(ValueError, match="セグメントが空です"):
            builder.build_draft_prompt(transcription)

    def test_build_draft_prompt_with_empty_text_raises_error(self):
        """空のテキストでエラーが発生することをテスト"""
        segments = [TranscriptionSegment(0.0, 10.0, "テスト")]
        transcription = TranscriptionResult(segments, "")
        builder = PromptBuilder()

        with pytest.raises(ValueError, match="全体テキストが空です"):
            builder.build_draft_prompt(transcription)


class TestTimeFormatting:
    """時刻フォーマット機能テスト"""

    def test_format_time_to_hms_basic(self):
        """基本的な時刻フォーマットテスト"""
        builder = PromptBuilder()

        assert builder._format_time_to_hms(0.0) == "00:00:00"
        assert builder._format_time_to_hms(65.0) == "00:01:05"
        assert builder._format_time_to_hms(3661.0) == "01:01:01"

    def test_format_segments_with_time(self):
        """時刻付きセグメントフォーマットテスト"""
        segments = [
            TranscriptionSegment(0.0, 30.0, "最初の内容"),
            TranscriptionSegment(30.0, 90.0, "次の内容"),
        ]
        builder = PromptBuilder()

        formatted = builder._format_segments(segments)

        assert "[00:00:00 - 00:00:30]" in formatted
        assert "[00:00:30 - 00:01:30]" in formatted
        assert "最初の内容" in formatted
        assert "次の内容" in formatted

    def test_format_segments_with_multiple_segments(self):
        """複数セグメントのフォーマットテスト"""
        segments = [
            TranscriptionSegment(0.0, 5.0, "皆さん、これ知ってました？実は..."),
            TranscriptionSegment(
                5.0, 15.0, "今日お話しするのは、誰も教えてくれない秘密の方法です"
            ),
            TranscriptionSegment(
                15.0, 30.0, "まず最初のポイントは、タイミングが全てということ"
            ),
        ]
        builder = PromptBuilder()

        formatted = builder._format_segments(segments)

        lines = formatted.split("\n")
        assert len(lines) == 3
        assert "  1. [00:00:00 - 00:00:05]" in lines[0]
        assert "  2. [00:00:05 - 00:00:15]" in lines[1]
        assert "  3. [00:00:15 - 00:00:30]" in lines[2]


class TestPromptBuilderIntegration:
    """PromptBuilderの統合テスト"""

    @pytest.fixture
    def sample_transcription(self):
        """テスト用文字起こしデータ"""
        segments = [
            TranscriptionSegment(0.0, 5.0, "皆さん、これ知ってました？実は..."),
            TranscriptionSegment(
                5.0, 15.0, "今日お話しするのは、誰も教えてくれない秘密の方法です"
            ),
            TranscriptionSegment(
                15.0, 30.0, "まず最初のポイントは、タイミングが全てということ"
            ),
            TranscriptionSegment(
                30.0, 45.0, "次に重要なのは、相手の心理を理解すること"
            ),
            TranscriptionSegment(
                45.0, 60.0, "最後に、これを実践すれば必ず結果が出ます"
            ),
        ]
        return TranscriptionResult(
            segments=segments,
            full_text=(
                "皆さん、これ知ってました？実は...今日お話しするのは、誰も教えてくれない秘密の方法です。"
                "まず最初のポイントは、タイミングが全てということ。次に重要なのは、相手の心理を理解すること。"
                "最後に、これを実践すれば必ず結果が出ます。"
            ),
        )

    def test_build_draft_prompt_integration(self, sample_transcription):
        """統合テスト: 実際のデータでプロンプト生成"""
        builder = PromptBuilder()
        prompt = builder.build_draft_prompt(sample_transcription)

        assert isinstance(prompt, str)
        assert len(prompt) > 1000

        assert "皆さん、これ知ってました？" in prompt
        assert "誰も教えてくれない秘密の方法" in prompt
        assert "[00:00:00 - 00:00:05]" in prompt
        assert "[00:00:45 - 00:01:00]" in prompt

        assert "冒頭2秒でインパクト" in prompt
        assert "視聴時間をハック" in prompt
        assert "JSON形式以外の出力は一切含めず" in prompt

    def test_prompt_structure_completeness(self, sample_transcription):
        """プロンプト構造の完全性テスト"""
        builder = PromptBuilder()
        prompt = builder.build_draft_prompt(sample_transcription)

        required_sections = [
            "# 依頼内容",
            "# 動画書き起こし",
            "## 全体テキスト",
            "## タイムスタンプ付きセグメント",
            "# 次の点をjson形式で",
            "# ショート動画を作る主なポイント",
            "## 冒頭2秒でインパクト",
            "## 視聴時間をハック",
        ]

        for section in required_sections:
            assert (
                section in prompt
            ), f"必須セクション '{section}' がプロンプトに含まれていません"

    def test_json_format_specification(self, sample_transcription):
        """JSON形式指定の確認テスト"""
        builder = PromptBuilder()
        prompt = builder.build_draft_prompt(sample_transcription)

        json_fields = [
            "first_impact",
            "last_conclusion",
            "summary",
            "time_start",
            "time_end",
            "title",
            "caption",
            "key_points",
        ]

        for field in json_fields:
            assert (
                f'"{field}"' in prompt
            ), f"JSONフィールド '{field}' がプロンプトに含まれていません"
