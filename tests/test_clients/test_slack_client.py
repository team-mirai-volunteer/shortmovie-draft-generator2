"""SlackClientのテスト"""

import json
import unittest
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.clients.slack_client import (
    MessageValidationError,
    ProcessResult,
    SlackClient,
    SlackWebHookError,
)


class TestSlackClient(unittest.TestCase):
    """SlackClientのテストケース"""

    def setUp(self):
        """テスト前の準備"""
        self.valid_webhook_url = "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
        self.invalid_webhook_url = "https://example.com/webhook"
        self.client = SlackClient(self.valid_webhook_url)

    def test_init_with_valid_url(self):
        """有効なWebHook URLでの初期化テスト"""
        client = SlackClient(self.valid_webhook_url)
        assert client.webhook_url == self.valid_webhook_url
        assert client.timeout == 30  # デフォルトタイムアウト

        # カスタムタイムアウトでの初期化
        client = SlackClient(self.valid_webhook_url, timeout=60)
        assert client.timeout == 60

    def test_init_with_invalid_url(self):
        """無効なWebHook URLでの初期化テスト"""
        # 空のURL
        with pytest.raises(ValueError) as cm:
            SlackClient("")
        assert str(cm.value) == "WebHook URLが指定されていません"

        # 無効なURL形式
        with pytest.raises(ValueError) as cm:
            SlackClient(self.invalid_webhook_url)
        assert str(cm.value) == "無効なSlack WebHook URLです"

    @patch("requests.post")
    def test_send_message_success(self, mock_post):
        """メッセージ送信成功テスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "ok"
        mock_post.return_value = mock_response

        # テスト実行
        self.client.send_message("テストメッセージ")

        # 検証
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == self.valid_webhook_url
        assert call_args[1]["timeout"] == 30
        assert call_args[1]["headers"] == {"Content-Type": "application/json"}

        # ペイロードの検証
        payload = json.loads(json.dumps(call_args[1]["json"]))
        assert payload["text"] == "テストメッセージ"

    @patch("requests.post")
    def test_send_process_notification_success(self, mock_post):
        """処理完了通知送信成功テスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "ok"
        mock_post.return_value = mock_response

        # 固定タイムスタンプを使用
        current_time = "2025-07-11 13:00:00"
        result = ProcessResult(
            success=True,
            process_name="テスト処理",
            file_name="test.mp4",
            processing_time=10.5,
            timestamp=current_time,
        )

        # テスト実行
        self.client.send_process_notification(result)

        # 検証
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == self.valid_webhook_url

        # ペイロードの検証
        payload = json.loads(json.dumps(call_args[1]["json"]))
        assert payload["text"] == ":white_check_mark: テスト処理 - 成功"
        assert len(payload["attachments"]) == 1
        assert payload["attachments"][0]["color"] == "good"

        # フィールドの検証
        fields = payload["attachments"][0]["fields"]
        assert len(fields) == 3  # ファイル名、処理時間、実行時刻

        # フィールド内容の検証
        field_dict = {field["title"]: field["value"] for field in fields}
        assert field_dict["ファイル名"] == "test.mp4"
        assert field_dict["処理時間"] == "10.5秒"
        assert field_dict["実行時刻"] == current_time

    @patch("requests.post")
    def test_send_process_notification_failure(self, mock_post):
        """処理失敗通知送信テスト"""
        # モックの設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "ok"
        mock_post.return_value = mock_response

        # 失敗結果の作成
        result = ProcessResult(
            success=False,
            process_name="テスト処理",
            file_name="error.mp4",
            error_message="テストエラーが発生しました",
            timestamp="2025-07-11 13:00:00",
        )

        # テスト実行
        self.client.send_process_notification(result)

        # 検証
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # ペイロードの検証
        payload = json.loads(json.dumps(call_args[1]["json"]))
        assert payload["text"] == ":x: テスト処理 - 失敗"
        assert payload["attachments"][0]["color"] == "danger"

        # エラーメッセージの検証
        fields = payload["attachments"][0]["fields"]
        error_field = next((f for f in fields if f["title"] == "エラー内容"), None)
        assert error_field is not None
        assert error_field["value"] == "テストエラーが発生しました"

    def test_validate_message(self):
        """メッセージバリデーションテスト"""
        # 空のメッセージ
        with pytest.raises(MessageValidationError) as cm:
            self.client._validate_message("")
        assert str(cm.value) == "メッセージが空です"

        # 長すぎるメッセージ
        long_message = "a" * 40001
        with pytest.raises(MessageValidationError) as cm:
            self.client._validate_message(long_message)
        assert str(cm.value) == "メッセージが長すぎます（40,000文字以内）"

        # 正常なメッセージ
        self.client._validate_message("正常なメッセージ")  # 例外が発生しないことを確認

    def test_validate_process_result(self):
        """ProcessResultバリデーションテスト"""
        # プロセス名が空
        result = ProcessResult(success=True, process_name="")
        with pytest.raises(MessageValidationError) as cm:
            self.client._validate_process_result(result)
        assert str(cm.value) == "プロセス名が指定されていません"
        assert cm.value.field_name == "process_name"

        # 処理時間が負数
        result = ProcessResult(success=True, process_name="テスト", processing_time=-1.0)
        with pytest.raises(MessageValidationError) as cm:
            self.client._validate_process_result(result)
        assert str(cm.value) == "処理時間は0以上である必要があります"
        assert cm.value.field_name == "processing_time"

        # 正常なProcessResult
        result = ProcessResult(success=True, process_name="テスト", processing_time=10.0)
        self.client._validate_process_result(result)  # 例外が発生しないことを確認

    @patch("requests.post")
    def test_webhook_api_error(self, mock_post):
        """WebHook API呼び出しエラーテスト"""
        # エラーレスポンスの設定
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "invalid_payload"
        mock_post.return_value = mock_response

        # テスト実行
        with pytest.raises(SlackWebHookError) as cm:
            self.client.send_message("テストメッセージ")

        # 例外の検証
        assert str(cm.value) == "Slack WebHook API呼び出しに失敗しました: 400 - invalid_payload"
        assert cm.value.status_code == 400

    @patch("requests.post")
    @patch("time.sleep")  # sleep関数をモック化して待機をスキップ
    def test_rate_limit_retry(self, mock_sleep, mock_post):
        """レート制限時のリトライテスト"""
        # 1回目: レート制限エラー
        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "30"}
        rate_limit_response.text = "rate_limited"

        # 2回目: 成功
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.text = "ok"

        # モックの設定（1回目はレート制限、2回目は成功）
        mock_post.side_effect = [rate_limit_response, success_response]

        # テスト実行
        self.client.send_message("テストメッセージ")

        # 検証
        assert mock_post.call_count == 2  # 2回呼ばれたことを確認
        mock_sleep.assert_called_once_with(30)  # Retry-Afterの値でsleepが呼ばれたことを確認

    @patch("requests.post")
    @patch("time.sleep")
    def test_network_error_retry(self, mock_sleep, mock_post):
        """ネットワークエラー時のリトライテスト"""
        # 1回目と2回目: ネットワークエラー
        network_error = requests.exceptions.ConnectionError("Connection refused")

        # 3回目: 成功
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.text = "ok"

        # モックの設定
        mock_post.side_effect = [network_error, network_error, success_response]

        # テスト実行
        self.client.send_message("テストメッセージ")

        # 検証
        assert mock_post.call_count == 3  # 3回呼ばれたことを確認
        assert mock_sleep.call_count == 2  # 2回sleepが呼ばれたことを確認
        # 指数バックオフの検証
        mock_sleep.assert_any_call(1)  # 1回目のリトライ: 2^0 = 1秒
        mock_sleep.assert_any_call(2)  # 2回目のリトライ: 2^1 = 2秒

    @patch("requests.post")
    @patch("time.sleep")
    def test_max_retries_exceeded(self, mock_sleep, mock_post):
        """最大リトライ回数超過テスト"""
        # すべての試行でネットワークエラー
        network_error = requests.exceptions.ConnectionError("Connection refused")
        mock_post.side_effect = [network_error, network_error, network_error]

        # テスト実行
        with pytest.raises(SlackWebHookError) as cm:
            self.client.send_message("テストメッセージ")

        # 例外の検証
        assert "Slack WebHook API呼び出しが3回失敗しました" in str(cm.value)
        assert "Connection refused" in str(cm.value)

        # 検証
        assert mock_post.call_count == 3  # 3回呼ばれたことを確認
        assert mock_sleep.call_count == 2  # 2回sleepが呼ばれたことを確認


if __name__ == "__main__":
    unittest.main()
