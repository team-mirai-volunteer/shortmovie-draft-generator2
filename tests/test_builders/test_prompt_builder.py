"""prompt_builder.pyのテスト"""

import pytest

from src.builders.prompt_builder import PromptBuilder
from src.models.transcription import TranscriptionResult, TranscriptionSegment


class TestPromptBuilder:
    """PromptBuilderの基本機能テスト"""

    def test_instance_creation(self):
        """インスタンス生成テスト"""
        builder = PromptBuilder()
        assert builder is not None

    def test_build_hooks_prompt_basic(self):
        """基本的なプロンプト生成テスト"""
        segments = [TranscriptionSegment(0.0, 10.0, "テスト内容")]
        transcription = TranscriptionResult(segments, "テスト内容")
        builder = PromptBuilder()

        prompt = builder.build_hooks_prompt(transcription)

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "テスト内容" in prompt
        assert "出力フォーマット" in prompt
        assert "first_hook" in prompt

    def test_prompt_contains_best_practices(self):
        """プロンプトにベストプラクティスが含まれているかテスト"""
        segments = [TranscriptionSegment(0.0, 10.0, "テスト")]
        transcription = TranscriptionResult(segments, "テスト")
        builder = PromptBuilder()

        prompt = builder.build_hooks_prompt(transcription)

        assert "フックを作るための TIPS" in prompt
        assert "ショート動画バズのコツ" in prompt
        assert "驚きで惹きつける（Surprise）" in prompt

    def test_validation_empty_segments(self):
        """空のセグメントでのバリデーションテスト"""
        transcription = TranscriptionResult([], "テスト")
        builder = PromptBuilder()

        with pytest.raises(ValueError) as exc_info:
            builder.build_hooks_prompt(transcription)
        assert "セグメントが空です" in str(exc_info.value)

    def test_validation_empty_full_text(self):
        """空の全体テキストでのバリデーションテスト"""
        segments = [TranscriptionSegment(0.0, 10.0, "テスト")]
        transcription = TranscriptionResult(segments, "")
        builder = PromptBuilder()

        with pytest.raises(ValueError) as exc_info:
            builder.build_hooks_prompt(transcription)
        assert "全体テキストが空です" in str(exc_info.value)

    def test_validation_whitespace_only_full_text(self):
        """空白のみの全体テキストでのバリデーションテスト"""
        segments = [TranscriptionSegment(0.0, 10.0, "テスト")]
        transcription = TranscriptionResult(segments, "   \n\t  ")
        builder = PromptBuilder()

        with pytest.raises(ValueError) as exc_info:
            builder.build_hooks_prompt(transcription)
        assert "全体テキストが空です" in str(exc_info.value)

    def test_string_representation(self):
        """文字列表現のテスト"""
        builder = PromptBuilder()
        str_repr = str(builder)
        assert "PromptBuilder" in str_repr

    def test_field_types(self):
        """フィールドの型の正確性のテスト"""
        segments = [TranscriptionSegment(0.0, 10.0, "テスト")]
        transcription = TranscriptionResult(segments, "テスト")
        builder = PromptBuilder()

        prompt = builder.build_hooks_prompt(transcription)
        assert isinstance(prompt, str)


class TestTimeFormatting:
    """時刻フォーマット機能テスト"""

    def test_format_time_to_hms_basic(self):
        """基本的な時刻フォーマットテスト"""
        builder = PromptBuilder()

        assert builder._format_time_to_hms(0.0) == "00:00:00"
        assert builder._format_time_to_hms(65.0) == "00:01:05"
        assert builder._format_time_to_hms(3661.0) == "01:01:01"

    def test_format_time_to_hms_edge_cases(self):
        """時刻フォーマットのエッジケーステスト"""
        builder = PromptBuilder()

        assert builder._format_time_to_hms(59.0) == "00:00:59"
        assert builder._format_time_to_hms(60.0) == "00:01:00"
        assert builder._format_time_to_hms(3599.0) == "00:59:59"
        assert builder._format_time_to_hms(3600.0) == "01:00:00"

    def test_format_time_to_hms_fractional_seconds(self):
        """小数点を含む秒数のフォーマットテスト"""
        builder = PromptBuilder()

        assert builder._format_time_to_hms(65.7) == "00:01:05"
        assert builder._format_time_to_hms(3661.9) == "01:01:01"

    def test_format_segments_basic(self):
        """基本的なセグメントフォーマットテスト"""
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

    def test_format_segments_numbering(self):
        """セグメント番号付けのテスト"""
        segments = [
            TranscriptionSegment(0.0, 10.0, "第一"),
            TranscriptionSegment(10.0, 20.0, "第二"),
            TranscriptionSegment(20.0, 30.0, "第三"),
        ]
        builder = PromptBuilder()

        formatted = builder._format_segments(segments)
        lines = formatted.split("\n")

        assert "  1." in lines[0]
        assert "  2." in lines[1]
        assert "  3." in lines[2]

    def test_format_segments_empty_list(self):
        """空のセグメントリストのフォーマットテスト"""
        builder = PromptBuilder()
        formatted = builder._format_segments([])
        assert formatted == ""

    def test_format_segments_single_item(self):
        """単一セグメントのフォーマットテスト"""
        segments = [TranscriptionSegment(0.0, 10.0, "単一内容")]
        builder = PromptBuilder()

        formatted = builder._format_segments(segments)

        assert "[00:00:00 - 00:00:10]" in formatted
        assert "単一内容" in formatted
        assert "  1." in formatted


class TestSampleData:
    """サンプルデータを使った統合テスト"""

    def test_short_video_sample_data(self):
        """ショート動画向けサンプルデータでのテスト"""
        short_video_segments = [
            TranscriptionSegment(0.0, 5.0, "皆さん、これ知ってました？実は..."),
            TranscriptionSegment(5.0, 15.0, "今日お話しするのは、誰も教えてくれない秘密の方法です"),
            TranscriptionSegment(15.0, 30.0, "まず最初のポイントは、タイミングが全てということ"),
            TranscriptionSegment(30.0, 45.0, "次に重要なのは、相手の心理を理解すること"),
            TranscriptionSegment(45.0, 60.0, "最後に、これを実践すれば必ず結果が出ます"),
        ]

        short_video_transcription = TranscriptionResult(
            segments=short_video_segments,
            full_text=(
                "皆さん、これ知ってました？実は...今日お話しするのは、誰も教えてくれない秘密の方法です。まず最初のポイントは、タイミングが全てということ。次に重要なのは、相手の心理を理解すること。最後に、これを実践すれば必ず結果が出ます。"
            ),
        )

        builder = PromptBuilder()
        prompt = builder.build_hooks_prompt(short_video_transcription)

        assert isinstance(prompt, str)
        assert len(prompt) > 0

        assert "皆さん、これ知ってました？" in prompt
        assert "秘密の方法" in prompt
        assert "タイミングが全て" in prompt

        assert "[00:00:00 - 00:00:05]" in prompt
        assert "[00:00:05 - 00:00:15]" in prompt
        assert "[00:00:45 - 00:01:00]" in prompt

        assert "フックを作るための TIPS" in prompt
        assert "ショート動画バズのコツ" in prompt
        assert "出力フォーマット" in prompt

    def test_realistic_usage_pattern(self):
        """実際の使用パターンに近いテスト"""
        segments = [
            TranscriptionSegment(0.0, 2.1, "皆さん、こんにちは"),
            TranscriptionSegment(2.1, 5.8, "今日はPythonについて"),
            TranscriptionSegment(5.8, 9.2, "お話ししたいと思います"),
            TranscriptionSegment(9.2, 12.5, "まず基本的な文法から"),
            TranscriptionSegment(12.5, 15.0, "始めていきましょう"),
        ]

        full_text = "皆さん、こんにちは今日はPythonについてお話ししたいと思いますまず基本的な文法から始めていきましょう"

        transcription = TranscriptionResult(segments=segments, full_text=full_text)

        builder = PromptBuilder()
        prompt = builder.build_hooks_prompt(transcription)

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert full_text in prompt

        assert "[00:00:00 - 00:00:02]" in prompt
        assert "[00:00:02 - 00:00:05]" in prompt
        assert "[00:00:12 - 00:00:15]" in prompt

        assert "皆さん、こんにちは" in prompt
        assert "Pythonについて" in prompt
        assert "始めていきましょう" in prompt

    def test_long_duration_formatting(self):
        """長時間動画のフォーマットテスト"""
        segments = [
            TranscriptionSegment(0.0, 3600.0, "1時間の内容"),
            TranscriptionSegment(3600.0, 7200.0, "2時間目の内容"),
        ]

        transcription = TranscriptionResult(segments=segments, full_text="1時間の内容2時間目の内容")

        builder = PromptBuilder()
        prompt = builder.build_hooks_prompt(transcription)

        assert "[01:00:00 - 02:00:00]" in prompt
        assert "[00:00:00 - 01:00:00]" in prompt

    def test_prompt_template_consistency(self):
        """プロンプトテンプレートの一貫性テスト"""
        segments = [TranscriptionSegment(0.0, 10.0, "テスト")]
        transcription = TranscriptionResult(segments, "テスト")
        builder = PromptBuilder()

        prompt = builder.build_hooks_prompt(transcription)

        required_sections = [
            "# 依頼内容",
            "# 動画書き起こし",
            "## 全体テキスト",
            "## タイムスタンプ付きセグメント",
            "# 出力フォーマット",
            "# フックを作るための TIPS",
        ]

        for section in required_sections:
            assert section in prompt

        required_json_fields = [
            "first_hook",
            "second_hook",
            "third_hook",
            "summary",
        ]

        for field in required_json_fields:
            assert field in prompt
