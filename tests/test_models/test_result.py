"""result.pyのテスト"""

from src.models.result import GenerateResult


class TestGenerateResult:
    """GenerateResultのテストクラス"""

    def test_instance_creation_success(self):
        """成功時のインスタンス生成のテスト"""
        result = GenerateResult(
            draft_file_path="output/draft.md",
            subtitle_file_path="output/subtitle.srt",
            success=True,
        )

        assert result.draft_file_path == "output/draft.md"
        assert result.subtitle_file_path == "output/subtitle.srt"
        assert result.success is True
        assert result.error_message is None

    def test_instance_creation_failure(self):
        """失敗時のインスタンス生成のテスト"""
        result = GenerateResult(
            draft_file_path="",
            subtitle_file_path="",
            success=False,
            error_message="API呼び出しに失敗しました",
        )

        assert result.draft_file_path == ""
        assert result.subtitle_file_path == ""
        assert result.success is False
        assert result.error_message == "API呼び出しに失敗しました"

    def test_equality_comparison(self):
        """等価性比較のテスト"""
        result1 = GenerateResult(
            draft_file_path="output/draft.md",
            subtitle_file_path="output/subtitle.srt",
            success=True,
        )
        result2 = GenerateResult(
            draft_file_path="output/draft.md",
            subtitle_file_path="output/subtitle.srt",
            success=True,
        )
        result3 = GenerateResult(
            draft_file_path="output/draft.md",
            subtitle_file_path="output/subtitle.srt",
            success=False,
            error_message="エラー",
        )

        assert result1 == result2
        assert result1 != result3

    def test_string_representation(self):
        """文字列表現のテスト"""
        result = GenerateResult(
            draft_file_path="output/draft.md",
            subtitle_file_path="output/subtitle.srt",
            success=True,
        )
        str_repr = str(result)

        assert "GenerateResult" in str_repr
        assert "output/draft.md" in str_repr
        assert "True" in str_repr

    def test_success_flag_validation(self):
        """成功フラグの検証テスト"""
        # 成功時
        success_result = GenerateResult(
            draft_file_path="output/draft.md",
            subtitle_file_path="output/subtitle.srt",
            success=True,
        )
        assert success_result.success is True

        # 失敗時
        failure_result = GenerateResult(
            draft_file_path="",
            subtitle_file_path="",
            success=False,
            error_message="エラーが発生しました",
        )
        assert failure_result.success is False

    def test_field_types(self):
        """フィールドの型の正確性のテスト"""
        result = GenerateResult(
            draft_file_path="output/draft.md",
            subtitle_file_path="output/subtitle.srt",
            success=True,
            error_message=None,
        )

        assert isinstance(result.draft_file_path, str)
        assert isinstance(result.subtitle_file_path, str)
        assert isinstance(result.success, bool)
        assert result.error_message is None or isinstance(result.error_message, str)

    def test_optional_error_message(self):
        """オプショナルなエラーメッセージのテスト"""
        # エラーメッセージなし（デフォルト）
        result_no_error = GenerateResult(
            draft_file_path="output/draft.md",
            subtitle_file_path="output/subtitle.srt",
            success=True,
        )
        assert result_no_error.error_message is None

        # エラーメッセージあり
        result_with_error = GenerateResult(
            draft_file_path="",
            subtitle_file_path="",
            success=False,
            error_message="ファイルが見つかりません",
        )
        assert result_with_error.error_message == "ファイルが見つかりません"

        # 明示的にNoneを設定
        result_explicit_none = GenerateResult(
            draft_file_path="output/draft.md",
            subtitle_file_path="output/subtitle.srt",
            success=True,
            error_message=None,
        )
        assert result_explicit_none.error_message is None

    def test_empty_file_paths(self):
        """空のファイルパスのテスト"""
        result = GenerateResult(
            draft_file_path="",
            subtitle_file_path="",
            success=False,
            error_message="処理に失敗しました",
        )

        assert result.draft_file_path == ""
        assert result.subtitle_file_path == ""
        assert result.success is False
        assert result.error_message == "処理に失敗しました"

    def test_long_file_paths(self):
        """長いファイルパスのテスト"""
        long_draft_path = (
            "very/long/path/to/output/directory/with/many/subdirectories/draft.md"
        )
        long_subtitle_path = (
            "very/long/path/to/output/directory/with/many/subdirectories/subtitle.srt"
        )

        result = GenerateResult(
            draft_file_path=long_draft_path,
            subtitle_file_path=long_subtitle_path,
            success=True,
        )

        assert result.draft_file_path == long_draft_path
        assert result.subtitle_file_path == long_subtitle_path
        assert result.success is True


class TestSampleData:
    """サンプルデータを使った統合テスト"""

    def test_sample_success_result(self):
        """設計書の成功例サンプルデータでのテスト"""
        result = GenerateResult(
            draft_file_path="output/draft.md",
            subtitle_file_path="output/subtitle.srt",
            success=True,
        )

        # 基本的な検証
        assert result.draft_file_path == "output/draft.md"
        assert result.subtitle_file_path == "output/subtitle.srt"
        assert result.success is True
        assert result.error_message is None

        # 成功時の典型的な使用パターン
        if result.success:
            assert result.draft_file_path != ""
            assert result.subtitle_file_path != ""
            assert result.error_message is None

    def test_sample_failure_result(self):
        """設計書の失敗例サンプルデータでのテスト"""
        error_result = GenerateResult(
            draft_file_path="",
            subtitle_file_path="",
            success=False,
            error_message="API呼び出しに失敗しました",
        )

        # 基本的な検証
        assert error_result.draft_file_path == ""
        assert error_result.subtitle_file_path == ""
        assert error_result.success is False
        assert error_result.error_message == "API呼び出しに失敗しました"

        # 失敗時の典型的な使用パターン
        if not error_result.success:
            assert error_result.error_message is not None
            assert error_result.error_message != ""

    def test_realistic_usage_patterns(self):
        """実際の使用パターンに近いテスト"""
        # 様々な成功パターン
        success_cases = [
            {
                "draft_file_path": "output/2025-01-10_draft.md",
                "subtitle_file_path": "output/2025-01-10_subtitle.srt",
                "success": True,
                "error_message": None,
            },
            {
                "draft_file_path": "/tmp/shortmovie/draft_001.md",
                "subtitle_file_path": "/tmp/shortmovie/subtitle_001.srt",
                "success": True,
                "error_message": None,
            },
            {
                "draft_file_path": "C:\\Users\\user\\Documents\\output\\draft.md",
                "subtitle_file_path": "C:\\Users\\user\\Documents\\output\\subtitle.srt",
                "success": True,
                "error_message": None,
            },
        ]

        for case in success_cases:
            result = GenerateResult(**case)
            assert result.success is True
            assert result.error_message is None
            assert result.draft_file_path != ""
            assert result.subtitle_file_path != ""

        # 様々な失敗パターン
        failure_cases = [
            {
                "draft_file_path": "",
                "subtitle_file_path": "",
                "success": False,
                "error_message": "OpenAI APIキーが設定されていません",
            },
            {
                "draft_file_path": "",
                "subtitle_file_path": "",
                "success": False,
                "error_message": "入力動画ファイルが見つかりません",
            },
            {
                "draft_file_path": "",
                "subtitle_file_path": "",
                "success": False,
                "error_message": "ネットワークエラーが発生しました",
            },
            {
                "draft_file_path": "",
                "subtitle_file_path": "",
                "success": False,
                "error_message": "出力ディレクトリへの書き込み権限がありません",
            },
        ]

        for case in failure_cases:
            result = GenerateResult(**case)
            assert result.success is False
            assert result.error_message is not None
            assert result.error_message != ""
            assert result.draft_file_path == ""
            assert result.subtitle_file_path == ""

    def test_partial_success_scenarios(self):
        """部分的成功シナリオのテスト"""
        # 企画書は生成されたが字幕ファイルの生成に失敗した場合
        partial_result = GenerateResult(
            draft_file_path="output/draft.md",
            subtitle_file_path="",
            success=False,
            error_message="字幕ファイルの生成に失敗しました",
        )

        assert partial_result.draft_file_path == "output/draft.md"
        assert partial_result.subtitle_file_path == ""
        assert partial_result.success is False
        assert "字幕ファイル" in partial_result.error_message

        # 字幕ファイルは生成されたが企画書の生成に失敗した場合
        another_partial_result = GenerateResult(
            draft_file_path="",
            subtitle_file_path="output/subtitle.srt",
            success=False,
            error_message="企画書の生成に失敗しました",
        )

        assert another_partial_result.draft_file_path == ""
        assert another_partial_result.subtitle_file_path == "output/subtitle.srt"
        assert another_partial_result.success is False
        assert "企画書" in another_partial_result.error_message
