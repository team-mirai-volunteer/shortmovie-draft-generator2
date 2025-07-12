"""ChatGPTClientのテスト"""

import json
import os
from unittest.mock import Mock, patch

import pytest

from src.clients.chatgpt_client import (
    ChatGPTClient,
    JSONParseError,
    ValidationError,
)
from src.models.hooks import HookItem


class TestChatGPTClient:
    """ChatGPTClientのテストクラス"""

    def test_init_success(self):
        """正常な初期化のテスト"""
        client = ChatGPTClient("test-api-key")
        assert client.api_key == "test-api-key"
        assert client.model == "gpt-4"

    def test_init_custom_model(self):
        """カスタムモデル指定の初期化テスト"""
        client = ChatGPTClient("test-api-key", model="gpt-3.5-turbo")
        assert client.model == "gpt-3.5-turbo"

    def test_init_empty_api_key(self):
        """空のAPIキーでの初期化エラーテスト"""
        with pytest.raises(ValueError, match="APIキーが指定されていません"):
            ChatGPTClient("")

    def test_validate_prompt_empty(self):
        """空のプロンプトの検証エラーテスト"""
        client = ChatGPTClient("test-api-key")
        with pytest.raises(ValueError, match="プロンプトが空です"):
            client._validate_prompt("")

    def test_validate_prompt_too_long(self):
        """長すぎるプロンプトの検証エラーテスト"""
        client = ChatGPTClient("test-api-key")
        long_prompt = "a" * 100001
        with pytest.raises(ValueError, match="プロンプトが長すぎます"):
            client._validate_prompt(long_prompt)

    def test_parse_json_response_success(self):
        """正常なJSON解析のテスト"""
        client = ChatGPTClient("test-api-key")
        json_response = '{"items": [{"title": "test"}]}'
        result = client._parse_json_response(json_response)
        assert result == {"items": [{"title": "test"}]}

    def test_parse_json_response_with_markdown(self):
        """Markdownコードブロック付きJSON解析のテスト"""
        client = ChatGPTClient("test-api-key")
        json_response = '```json\n{"items": [{"title": "test"}]}\n```'
        result = client._parse_json_response(json_response)
        assert result == {"items": [{"title": "test"}]}

    def test_parse_json_response_invalid(self):
        """無効なJSON解析のエラーテスト"""
        client = ChatGPTClient("test-api-key")
        with pytest.raises(JSONParseError):
            client._parse_json_response("invalid json")

    def test_validate_hooks_response_structure_missing_items(self):
        """itemsフィールドが欠けているレスポンスの検証エラーテスト"""
        client = ChatGPTClient("test-api-key")
        with pytest.raises(ValidationError, match="'items'フィールドがありません"):
            client._validate_hooks_response_structure({})

    def test_validate_hooks_response_structure_items_not_list(self):
        """itemsがリストでないレスポンスの検証エラーテスト"""
        client = ChatGPTClient("test-api-key")
        with pytest.raises(ValidationError, match="'items'フィールドがリスト形式ではありません"):
            client._validate_hooks_response_structure({"items": "not a list"})

    def test_validate_hooks_response_structure_empty_items(self):
        """空のitemsの検証エラーテスト"""
        client = ChatGPTClient("test-api-key")
        with pytest.raises(ValidationError, match="'items'が空です"):
            client._validate_hooks_response_structure({"items": []})

    def test_validate_hooks_response_structure_missing_required_field(self):
        """必須フィールドが欠けているアイテムの検証エラーテスト"""
        client = ChatGPTClient("test-api-key")
        data = {"items": [{"title": "test"}]}
        with pytest.raises(ValidationError, match="必須フィールド"):
            client._validate_hooks_response_structure(data)

    def test_parse_time_to_seconds_success(self):
        """正常な時刻解析のテスト"""
        client = ChatGPTClient("test-api-key")
        assert client._parse_time_to_seconds("01:30:45") == 5445.0
        assert client._parse_time_to_seconds("00:00:30") == 30.0
        assert client._parse_time_to_seconds("02:00:00") == 7200.0

    def test_parse_time_to_seconds_invalid_format(self):
        """無効な時刻形式の解析エラーテスト"""
        client = ChatGPTClient("test-api-key")
        with pytest.raises(ValueError, match="時刻形式が無効です"):
            client._parse_time_to_seconds("invalid")

    def test_convert_to_hook_items_success(self):
        """正常なフック変換のテスト"""
        client = ChatGPTClient("test-api-key")
        data = {
            "items": [
                {
                    "first_hook": "最初のフック",
                    "second_hook": "2番目のフック",
                    "third_hook": "3番目のフック",
                    "last_conclusion": "結論",
                    "summary": "要約",
                },
            ],
        }

        hook_items = client._convert_to_hook_items(data)
        assert len(hook_items) == 1
        assert isinstance(hook_items[0], HookItem)
        assert hook_items[0].first_hook == "最初のフック"
        assert hook_items[0].second_hook == "2番目のフック"
        assert hook_items[0].summary == "要約"

    @patch("src.clients.chatgpt_client.OpenAI")
    def test_extract_hooks_success(self, mock_openai):
        """正常なフック抽出のテスト"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "items": [
                    {
                        "first_hook": "最初のフック",
                        "second_hook": "2番目のフック",
                        "third_hook": "3番目のフック",
                        "last_conclusion": "結論",
                        "summary": "要約",
                    },
                ],
            },
        )

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        client = ChatGPTClient("test-api-key")
        hook_items = client.extract_hooks("test prompt")

        assert len(hook_items) == 1
        assert hook_items[0].first_hook == "最初のフック"
        mock_client.chat.completions.create.assert_called_once()


@pytest.mark.integration
class TestChatGPTClientIntegration:
    """ChatGPTClientの統合テスト（実際のAPI呼び出し）"""

    def test_extract_hooks_real_api(self):
        """実際のChatGPT APIを使用した企画書生成テスト"""
        if not os.getenv("INTEGRATION_TEST"):
            pytest.skip("統合テストはINTEGRATION_TEST=trueの場合のみ実行")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEYが設定されていません")

        client = ChatGPTClient(api_key)

        test_prompt = """
        以下の動画の書き起こしテキストから、切り抜き動画として適切な部分の概要を抜き出してください。

        # 動画書き起こし
        ## 全体テキスト
        こんにちは、今日はショート動画の作り方について話します。まず最初に重要なのは冒頭の2秒です。

        ## タイムスタンプ付きセグメント
        1. [00:00:00 - 00:00:05] こんにちは、今日はショート動画の作り方について話します。
        2. [00:00:05 - 00:00:10] まず最初に重要なのは冒頭の2秒です。

        # 次の点をjson形式でアウトプットとして出してください
        {
          "items": [
            {
              "first_impact": "最初の2秒に含まれる、興味を惹くフレーズ",
              "last_conclusion": "動画の最後に来る結論",
              "summary": "動画の主題",
              "time_start": "開始時刻(hh:mm:ss)",
              "time_end": "終了時刻(hh:mm:ss)",
              "title": "魅力的なタイトル（30文字以内）",
              "caption": "SNS投稿用キャプション（100文字以内、ハッシュタグ含む）",
              "key_points": ["重要なポイント1", "重要なポイント2"]
            }
          ]
        }
        """

        proposals = client.extract_hooks(test_prompt)

        assert len(proposals) > 0
        assert isinstance(proposals[0], HookItem)
        assert proposals[0].first_hook
        assert proposals[0].summary
        assert proposals[0].last_conclusion
