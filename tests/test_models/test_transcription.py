"""transcription.pyのテスト"""

from src.models.transcription import TranscriptionResult, TranscriptionSegment


class TestTranscriptionSegment:
    """TranscriptionSegmentのテストクラス"""

    def test_instance_creation(self):
        """インスタンス生成のテスト"""
        segment = TranscriptionSegment(0.0, 3.5, "こんにちは、今日は")

        assert segment.start_time == 0.0
        assert segment.end_time == 3.5
        assert segment.text == "こんにちは、今日は"

    def test_equality_comparison(self):
        """等価性比較のテスト"""
        segment1 = TranscriptionSegment(0.0, 3.5, "こんにちは、今日は")
        segment2 = TranscriptionSegment(0.0, 3.5, "こんにちは、今日は")
        segment3 = TranscriptionSegment(3.5, 7.2, "ショート動画について話します")

        assert segment1 == segment2
        assert segment1 != segment3

    def test_string_representation(self):
        """文字列表現のテスト"""
        segment = TranscriptionSegment(0.0, 3.5, "こんにちは、今日は")
        str_repr = str(segment)

        assert "TranscriptionSegment" in str_repr
        assert "0.0" in str_repr
        assert "3.5" in str_repr
        assert "こんにちは、今日は" in str_repr

    def test_time_consistency(self):
        """時刻の論理的整合性のテスト"""
        # 正常なケース
        segment = TranscriptionSegment(0.0, 3.5, "テスト")
        assert segment.start_time < segment.end_time

        # 同じ時刻のケース（瞬間的な発話）
        instant_segment = TranscriptionSegment(1.0, 1.0, "")
        assert instant_segment.start_time == instant_segment.end_time

    def test_field_types(self):
        """フィールドの型の正確性のテスト"""
        segment = TranscriptionSegment(0.0, 3.5, "テスト")

        assert isinstance(segment.start_time, float)
        assert isinstance(segment.end_time, float)
        assert isinstance(segment.text, str)


class TestTranscriptionResult:
    """TranscriptionResultのテストクラス"""

    def test_instance_creation(self):
        """インスタンス生成のテスト"""
        segments = [
            TranscriptionSegment(0.0, 3.5, "こんにちは、今日は"),
            TranscriptionSegment(3.5, 7.2, "ショート動画について話します"),
        ]
        result = TranscriptionResult(segments=segments, full_text="こんにちは、今日はショート動画について話します")

        assert len(result.segments) == 2
        assert result.full_text == "こんにちは、今日はショート動画について話します"

    def test_equality_comparison(self):
        """等価性比較のテスト"""
        segments1 = [TranscriptionSegment(0.0, 3.5, "テスト1")]
        segments2 = [TranscriptionSegment(0.0, 3.5, "テスト1")]
        segments3 = [TranscriptionSegment(0.0, 3.5, "テスト2")]

        result1 = TranscriptionResult(segments1, "テスト1")
        result2 = TranscriptionResult(segments2, "テスト1")
        result3 = TranscriptionResult(segments3, "テスト2")

        assert result1 == result2
        assert result1 != result3

    def test_string_representation(self):
        """文字列表現のテスト"""
        segments = [TranscriptionSegment(0.0, 3.5, "テスト")]
        result = TranscriptionResult(segments, "テスト")
        str_repr = str(result)

        assert "TranscriptionResult" in str_repr
        assert "テスト" in str_repr

    def test_empty_segments(self):
        """空のセグメントリストのテスト"""
        result = TranscriptionResult(segments=[], full_text="")

        assert len(result.segments) == 0
        assert result.full_text == ""

    def test_field_types(self):
        """フィールドの型の正確性のテスト"""
        segments = [TranscriptionSegment(0.0, 3.5, "テスト")]
        result = TranscriptionResult(segments, "テスト")

        assert isinstance(result.segments, list)
        assert isinstance(result.full_text, str)
        assert all(isinstance(seg, TranscriptionSegment) for seg in result.segments)


class TestSampleData:
    """サンプルデータを使った統合テスト"""

    def test_sample_transcription_data(self):
        """設計書のサンプルデータでのテスト"""
        sample_segments = [
            TranscriptionSegment(0.0, 3.5, "こんにちは、今日は"),
            TranscriptionSegment(3.5, 7.2, "ショート動画について話します"),
        ]

        sample_transcription = TranscriptionResult(segments=sample_segments, full_text="こんにちは、今日はショート動画について話します")

        # 基本的な検証
        assert len(sample_transcription.segments) == 2
        assert sample_transcription.full_text == "こんにちは、今日はショート動画について話します"

        # セグメントの内容検証
        first_segment = sample_transcription.segments[0]
        assert first_segment.start_time == 0.0
        assert first_segment.end_time == 3.5
        assert first_segment.text == "こんにちは、今日は"

        second_segment = sample_transcription.segments[1]
        assert second_segment.start_time == 3.5
        assert second_segment.end_time == 7.2
        assert second_segment.text == "ショート動画について話します"

        # 時系列の整合性確認
        assert first_segment.end_time == second_segment.start_time

    def test_realistic_usage_pattern(self):
        """実際の使用パターンに近いテスト"""
        # より長い文字起こし結果をシミュレート
        segments = [
            TranscriptionSegment(0.0, 2.1, "皆さん、こんにちは"),
            TranscriptionSegment(2.1, 5.8, "今日はPythonについて"),
            TranscriptionSegment(5.8, 9.2, "お話ししたいと思います"),
            TranscriptionSegment(9.2, 12.5, "まず基本的な文法から"),
            TranscriptionSegment(12.5, 15.0, "始めていきましょう"),
        ]

        full_text = "皆さん、こんにちは今日はPythonについてお話ししたいと思いますまず基本的な文法から始めていきましょう"

        transcription = TranscriptionResult(segments=segments, full_text=full_text)

        # 全体の検証
        assert len(transcription.segments) == 5
        assert transcription.full_text == full_text

        # 時系列の連続性確認
        for i in range(len(segments) - 1):
            current_segment = transcription.segments[i]
            next_segment = transcription.segments[i + 1]
            assert current_segment.end_time == next_segment.start_time

        # 全体の時間範囲確認
        total_duration = transcription.segments[-1].end_time - transcription.segments[0].start_time
        assert total_duration == 15.0
