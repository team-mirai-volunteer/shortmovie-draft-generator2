"""ChatGPTクライアントのテストモジュール"""

from unittest.mock import Mock, patch

import pytest

from src.clients.chatgpt_client import (
    ChatGPTAPIError,
    ChatGPTClient,
    ChatGPTClientError,
    JSONParseError,
    ValidationError,
)
from src.models.draft import DraftResult, ShortVideoProposal
from src.models.transcription import TranscriptionResult, TranscriptionSegment


class TestChatGPTClient:
    """ChatGPTクライアントのテストクラス"""

    def test_init_with_api_key(self):
        """APIキー指定での初期化テスト"""
        client = ChatGPTClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.model == "gpt-4o-mini"
        assert client.max_retries == 3
        assert client.retry_delay == 1.0

    @patch.dict("os.environ", {}, clear=True)
    def test_init_without_api_key_raises_error(self):
        """APIキーなしでの初期化エラーテスト"""
        with pytest.raises(ChatGPTClientError, match="OpenAI API key is required"):
            ChatGPTClient()

    def test_convert_time_to_seconds(self):
        """時間変換テスト"""
        client = ChatGPTClient(api_key="test-key")

        assert client._convert_time_to_seconds("01:23:45") == 5025.0
        assert client._convert_time_to_seconds("23:45") == 1425.0
        assert client._convert_time_to_seconds("45") == 45.0

        with pytest.raises(ValidationError):
            client._convert_time_to_seconds("invalid")

    def test_parse_json_response_with_code_block(self):
        """JSONコードブロック解析テスト"""
        client = ChatGPTClient(api_key="test-key")

        response_text = """```json
{
  "items": [
    {
      "title": "テストタイトル",
      "first_impact": "テストインパクト",
      "last_conclusion": "テスト結論",
      "summary": "テスト概要",
      "time_start": "00:00:00",
      "time_end": "00:01:00",
      "caption": "テストキャプション",
      "key_points": ["ポイント1", "ポイント2", "ポイント3"]
    }
  ]
}
```"""

        result = client._parse_json_response(response_text)
        assert "items" in result
        assert len(result["items"]) == 1
        assert result["items"][0]["title"] == "テストタイトル"

    def test_parse_json_response_without_code_block(self):
        """JSONコードブロックなし解析テスト"""
        client = ChatGPTClient(api_key="test-key")

        response_text = '{"test": "value"}'
        result = client._parse_json_response(response_text)
        assert result["test"] == "value"

    def test_parse_json_response_invalid_json(self):
        """無効JSON解析エラーテスト"""
        client = ChatGPTClient(api_key="test-key")

        with pytest.raises(JSONParseError):
            client._parse_json_response("invalid json")

    def test_validate_and_convert_proposals_success(self):
        """企画案バリデーション成功テスト"""
        client = ChatGPTClient(api_key="test-key")

        proposals_data = {
            "items": [
                {
                    "title": "テストタイトル1",
                    "first_impact": "テストインパクト1",
                    "last_conclusion": "テスト結論1",
                    "summary": "テスト概要1",
                    "time_start": "00:00:00",
                    "time_end": "00:01:00",
                    "caption": "テストキャプション1",
                    "key_points": ["ポイント1", "ポイント2", "ポイント3"],
                },
                {
                    "title": "テストタイトル2",
                    "first_impact": "テストインパクト2",
                    "last_conclusion": "テスト結論2",
                    "summary": "テスト概要2",
                    "time_start": "00:01:00",
                    "time_end": "00:02:00",
                    "caption": "テストキャプション2",
                    "key_points": ["ポイント1", "ポイント2", "ポイント3"],
                },
                {
                    "title": "テストタイトル3",
                    "first_impact": "テストインパクト3",
                    "last_conclusion": "テスト結論3",
                    "summary": "テスト概要3",
                    "time_start": "00:02:00",
                    "time_end": "00:03:00",
                    "caption": "テストキャプション3",
                    "key_points": ["ポイント1", "ポイント2", "ポイント3"],
                },
                {
                    "title": "テストタイトル4",
                    "first_impact": "テストインパクト4",
                    "last_conclusion": "テスト結論4",
                    "summary": "テスト概要4",
                    "time_start": "00:03:00",
                    "time_end": "00:04:00",
                    "caption": "テストキャプション4",
                    "key_points": ["ポイント1", "ポイント2", "ポイント3"],
                },
                {
                    "title": "テストタイトル5",
                    "first_impact": "テストインパクト5",
                    "last_conclusion": "テスト結論5",
                    "summary": "テスト概要5",
                    "time_start": "00:04:00",
                    "time_end": "00:05:00",
                    "caption": "テストキャプション5",
                    "key_points": ["ポイント1", "ポイント2", "ポイント3"],
                },
            ]
        }

        proposals = client._validate_and_convert_proposals(proposals_data)
        assert len(proposals) == 5
        assert all(isinstance(p, ShortVideoProposal) for p in proposals)
        assert proposals[0].title == "テストタイトル1"
        assert proposals[0].first_impact == "テストインパクト1"
        assert proposals[0].last_conclusion == "テスト結論1"
        assert proposals[0].summary == "テスト概要1"

    def test_validate_and_convert_proposals_missing_items_field(self):
        """企画案バリデーション失敗テスト（itemsフィールドなし）"""
        client = ChatGPTClient(api_key="test-key")

        proposals_data = {"data": []}

        with pytest.raises(
            ValidationError, match="レスポンスに'items'フィールドが含まれていません"
        ):
            client._validate_and_convert_proposals(proposals_data)

    def test_validate_and_convert_proposals_wrong_count(self):
        """企画案バリデーション失敗テスト（企画数が5個でない）"""
        client = ChatGPTClient(api_key="test-key")

        proposals_data = {
            "items": [
                {
                    "title": "テストタイトル1",
                    "first_impact": "テストインパクト1",
                    "last_conclusion": "テスト結論1",
                    "summary": "テスト概要1",
                    "time_start": "00:00:00",
                    "time_end": "00:01:00",
                    "caption": "テストキャプション1",
                    "key_points": ["ポイント1", "ポイント2", "ポイント3"],
                }
            ]
        }

        with pytest.raises(ValidationError, match="企画提案は5個である必要があります"):
            client._validate_and_convert_proposals(proposals_data)

    def test_validate_and_convert_proposals_missing_field(self):
        """企画案バリデーション失敗テスト（必須フィールドなし）"""
        client = ChatGPTClient(api_key="test-key")

        proposals_data = {
            "items": [
                {"title": "テストタイトル", "first_impact": "テストインパクト"},
                {"title": "テストタイトル", "first_impact": "テストインパクト"},
                {"title": "テストタイトル", "first_impact": "テストインパクト"},
                {"title": "テストタイトル", "first_impact": "テストインパクト"},
                {"title": "テストタイトル", "first_impact": "テストインパクト"},
            ]
        }

        with pytest.raises(ValidationError, match="必須フィールド"):
            client._validate_and_convert_proposals(proposals_data)

    @patch("src.clients.chatgpt_client.OpenAI")
    def test_make_api_call_success(self, mock_openai):
        """API呼び出し成功テスト"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "test response"

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        client = ChatGPTClient(api_key="test-key")

        messages = [{"role": "user", "content": "test"}]
        result = client._make_api_call(messages)

        assert result == "test response"
        mock_client.chat.completions.create.assert_called_once()

    @patch("src.clients.chatgpt_client.OpenAI")
    def test_make_api_call_retry_and_fail(self, mock_openai):
        """API呼び出しリトライ後失敗テスト"""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client

        client = ChatGPTClient(api_key="test-key", max_retries=2, retry_delay=0.1)

        messages = [{"role": "user", "content": "test"}]

        with pytest.raises(ChatGPTAPIError):
            client._make_api_call(messages)

        assert mock_client.chat.completions.create.call_count == 2

    @patch.object(ChatGPTClient, "_make_api_call")
    def test_generate_draft_success(self, mock_api_call):
        """ドラフト生成成功テスト"""
        mock_response = """```json
{
  "items": [
    {
      "title": "テストタイトル1",
      "first_impact": "テストインパクト1",
      "last_conclusion": "テスト結論1",
      "summary": "テスト概要1",
      "time_start": "00:00:00",
      "time_end": "00:01:00",
      "caption": "テストキャプション1",
      "key_points": ["ポイント1", "ポイント2", "ポイント3"]
    },
    {
      "title": "テストタイトル2",
      "first_impact": "テストインパクト2",
      "last_conclusion": "テスト結論2",
      "summary": "テスト概要2",
      "time_start": "00:01:00",
      "time_end": "00:02:00",
      "caption": "テストキャプション2",
      "key_points": ["ポイント1", "ポイント2", "ポイント3"]
    },
    {
      "title": "テストタイトル3",
      "first_impact": "テストインパクト3",
      "last_conclusion": "テスト結論3",
      "summary": "テスト概要3",
      "time_start": "00:02:00",
      "time_end": "00:03:00",
      "caption": "テストキャプション3",
      "key_points": ["ポイント1", "ポイント2", "ポイント3"]
    },
    {
      "title": "テストタイトル4",
      "first_impact": "テストインパクト4",
      "last_conclusion": "テスト結論4",
      "summary": "テスト概要4",
      "time_start": "00:03:00",
      "time_end": "00:04:00",
      "caption": "テストキャプション4",
      "key_points": ["ポイント1", "ポイント2", "ポイント3"]
    },
    {
      "title": "テストタイトル5",
      "first_impact": "テストインパクト5",
      "last_conclusion": "テスト結論5",
      "summary": "テスト概要5",
      "time_start": "00:04:00",
      "time_end": "00:05:00",
      "caption": "テストキャプション5",
      "key_points": ["ポイント1", "ポイント2", "ポイント3"]
    }
  ]
}
```"""
        mock_api_call.return_value = mock_response

        client = ChatGPTClient(api_key="test-key")
        transcription = TranscriptionResult(
            segments=[TranscriptionSegment(0.0, 120.0, "テスト文字起こし")],
            full_text="テスト文字起こし",
        )

        result = client.generate_draft(transcription)

        assert isinstance(result, DraftResult)
        assert len(result.proposals) == 5
        assert result.total_count == 5
        assert result.proposals[0].title == "テストタイトル1"
        assert result.proposals[0].first_impact == "テストインパクト1"
        assert result.proposals[0].last_conclusion == "テスト結論1"
        assert result.proposals[0].summary == "テスト概要1"

    @patch.object(ChatGPTClient, "_make_api_call")
    def test_generate_draft_from_prompt_success(self, mock_api_call):
        """プロンプトからドラフト生成成功テスト"""
        mock_response = """```json
{
  "items": [
    {
      "title": "テストタイトル1",
      "first_impact": "テストインパクト1",
      "last_conclusion": "テスト結論1",
      "summary": "テスト概要1",
      "time_start": "00:00:00",
      "time_end": "00:01:00",
      "caption": "テストキャプション1",
      "key_points": ["ポイント1", "ポイント2", "ポイント3"]
    },
    {
      "title": "テストタイトル2",
      "first_impact": "テストインパクト2",
      "last_conclusion": "テスト結論2",
      "summary": "テスト概要2",
      "time_start": "00:01:00",
      "time_end": "00:02:00",
      "caption": "テストキャプション2",
      "key_points": ["ポイント1", "ポイント2", "ポイント3"]
    },
    {
      "title": "テストタイトル3",
      "first_impact": "テストインパクト3",
      "last_conclusion": "テスト結論3",
      "summary": "テスト概要3",
      "time_start": "00:02:00",
      "time_end": "00:03:00",
      "caption": "テストキャプション3",
      "key_points": ["ポイント1", "ポイント2", "ポイント3"]
    },
    {
      "title": "テストタイトル4",
      "first_impact": "テストインパクト4",
      "last_conclusion": "テスト結論4",
      "summary": "テスト概要4",
      "time_start": "00:03:00",
      "time_end": "00:04:00",
      "caption": "テストキャプション4",
      "key_points": ["ポイント1", "ポイント2", "ポイント3"]
    },
    {
      "title": "テストタイトル5",
      "first_impact": "テストインパクト5",
      "last_conclusion": "テスト結論5",
      "summary": "テスト概要5",
      "time_start": "00:04:00",
      "time_end": "00:05:00",
      "caption": "テストキャプション5",
      "key_points": ["ポイント1", "ポイント2", "ポイント3"]
    }
  ]
}
```"""
        mock_api_call.return_value = mock_response

        client = ChatGPTClient(api_key="test-key")
        prompt = "テスト用プロンプト"

        result = client.generate_draft_from_prompt(prompt)

        assert isinstance(result, DraftResult)
        assert len(result.proposals) == 5
        assert result.total_count == 5
        assert result.proposals[0].title == "テストタイトル1"

    def test_validate_time_conversion_edge_cases(self):
        """時刻変換のエッジケーステスト"""
        client = ChatGPTClient(api_key="test-key")

        assert client._convert_time_to_seconds("0") == 0.0
        assert client._convert_time_to_seconds("00:00") == 0.0
        assert client._convert_time_to_seconds("00:00:00") == 0.0
        assert client._convert_time_to_seconds("1:30:45") == 5445.0

        with pytest.raises(ValidationError):
            client._convert_time_to_seconds("")

        with pytest.raises(ValidationError):
            client._convert_time_to_seconds("25:70:80")


class TestChatGPTClientIntegration:
    """ChatGPTクライアントの統合テスト"""

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

    @patch.object(ChatGPTClient, "_make_api_call")
    def test_end_to_end_draft_generation(self, mock_api_call, sample_transcription):
        """エンドツーエンドのドラフト生成テスト"""
        mock_response = """```json
{
  "items": [
    {
      "title": "秘密の方法を公開！",
      "first_impact": "皆さん、これ知ってました？",
      "last_conclusion": "必ず結果が出ます",
      "summary": "誰も教えてくれない秘密の方法で成功する",
      "time_start": "00:00:00",
      "time_end": "00:01:00",
      "caption": "秘密の成功法則を大公開！ #成功法則 #秘密",
      "key_points": ["タイミングが全て", "心理を理解", "実践が重要"]
    },
    {
      "title": "タイミングの重要性",
      "first_impact": "最初のポイントは",
      "last_conclusion": "タイミングが全てです",
      "summary": "成功にはタイミングが最も重要である",
      "time_start": "00:00:15",
      "time_end": "00:01:15",
      "caption": "成功のカギはタイミング！ #タイミング #成功",
      "key_points": ["適切な時期", "機会を逃さない", "準備の重要性"]
    },
    {
      "title": "心理学的アプローチ",
      "first_impact": "次に重要なのは",
      "last_conclusion": "心理を理解することです",
      "summary": "相手の心理を理解することで成功率が上がる",
      "time_start": "00:00:30",
      "time_end": "00:01:30",
      "caption": "心理学で成功率アップ！ #心理学 #コミュニケーション",
      "key_points": ["相手の立場", "感情の理解", "共感の力"]
    },
    {
      "title": "実践の力",
      "first_impact": "最後に",
      "last_conclusion": "実践すれば必ず結果が出ます",
      "summary": "理論だけでなく実践することで結果が生まれる",
      "time_start": "00:00:45",
      "time_end": "00:01:45",
      "caption": "実践こそが成功への道！ #実践 #行動力",
      "key_points": ["行動の重要性", "継続の力", "結果への確信"]
    },
    {
      "title": "完全攻略法",
      "first_impact": "これ知ってました？",
      "last_conclusion": "必ず成功できます",
      "summary": "秘密の方法を使えば誰でも成功できる",
      "time_start": "00:00:00",
      "time_end": "00:01:00",
      "caption": "完全攻略法を伝授！ #攻略法 #成功術",
      "key_points": ["秘密の方法", "確実な成功", "誰でもできる"]
    }
  ]
}
```"""
        mock_api_call.return_value = mock_response

        client = ChatGPTClient(api_key="test-key")
        result = client.generate_draft(sample_transcription, "追加コンテキスト情報")

        assert isinstance(result, DraftResult)
        assert len(result.proposals) == 5
        assert result.total_count == 5

        proposal = result.proposals[0]
        assert proposal.title == "秘密の方法を公開！"
        assert proposal.first_impact == "皆さん、これ知ってました？"
        assert proposal.last_conclusion == "必ず結果が出ます"
        assert proposal.summary == "誰も教えてくれない秘密の方法で成功する"
        assert proposal.start_time == 0.0
        assert proposal.end_time == 60.0
        assert len(proposal.key_points) == 3

    def test_prompt_builder_integration(self, sample_transcription):
        """PromptBuilderとの統合テスト"""
        client = ChatGPTClient(api_key="test-key")

        prompt = client._prompt_builder.build_draft_prompt(sample_transcription)

        assert isinstance(prompt, str)
        assert len(prompt) > 1000
        assert "皆さん、これ知ってました？" in prompt
        assert "冒頭2秒でインパクト" in prompt
        assert "視聴時間をハック" in prompt
