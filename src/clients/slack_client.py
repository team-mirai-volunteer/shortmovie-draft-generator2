"""Slack WebHook APIクライアントモジュール"""

import json
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
import datetime
import requests


@dataclass
class ProcessResult:
    """処理結果を表すデータクラス"""

    success: bool
    process_name: str
    file_name: Optional[str] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    timestamp: Optional[str] = None


class SlackClientError(Exception):
    """SlackClient関連のベース例外"""

    pass


class SlackWebHookError(SlackClientError):
    """Slack WebHook API呼び出しエラー"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        retry_after: Optional[int] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


class MessageValidationError(SlackClientError):
    """メッセージ内容検証エラー"""

    def __init__(self, message: str, field_name: Optional[str] = None):
        super().__init__(message)
        self.field_name = field_name


class SlackClient:
    """Slack WebHook APIクライアント

    WebHook URLを使用してSlackにメッセージを送信します。
    処理完了通知に特化し、統一されたフォーマットでメッセージを送信します。

    Example:
        >>> client = SlackClient("https://hooks.slack.com/services/...")
        >>> result = ProcessResult(
        ...     success=True,
        ...     process_name="ショート動画企画書生成",
        ...     file_name="input.mp4",
        ...     processing_time=45.2
        ... )
        >>> client.send_process_notification(result)
    """

    def __init__(self, webhook_url: str, timeout: int = 30) -> None:
        """SlackClientを初期化

        Args:
            webhook_url: Slack WebHook URL
            timeout: HTTP通信のタイムアウト時間（秒）

        Raises:
            ValueError: WebHook URLが無効な場合
        """
        # WebHook URLの妥当性チェック
        if not webhook_url or not webhook_url.strip():
            raise ValueError("WebHook URLが指定されていません")

        if not webhook_url.startswith("https://hooks.slack.com/"):
            raise ValueError("無効なSlack WebHook URLです")

        self.webhook_url = webhook_url
        self.timeout = timeout

    def send_process_notification(self, result: ProcessResult) -> None:
        """処理完了通知を送信

        Args:
            result: 処理結果情報

        Raises:
            SlackWebHookError: WebHook API呼び出しに失敗した場合
            MessageValidationError: メッセージ内容が無効な場合
        """
        self._validate_process_result(result)

        # タイムスタンプが指定されていない場合は現在時刻を使用
        if not result.timestamp:
            result.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        payload = self._build_process_notification_message(result)
        self._call_webhook_api(payload)

    def send_message(self, message: str) -> None:
        """カスタムメッセージを送信

        Args:
            message: 送信するメッセージ

        Raises:
            SlackWebHookError: WebHook API呼び出しに失敗した場合
            MessageValidationError: メッセージ内容が無効な場合
        """
        self._validate_message(message)

        payload = {"text": message}

        self._call_webhook_api(payload)

    def _build_process_notification_message(self, result: ProcessResult) -> Dict[str, Any]:
        """処理完了通知メッセージを構築

        Args:
            result: 処理結果情報

        Returns:
            Slack WebHook API用のペイロード
        """
        # 成功/失敗に応じたアイコンと色
        if result.success:
            icon = ":white_check_mark:"
            color = "good"  # 緑色
            status_text = "成功"
        else:
            icon = ":x:"
            color = "danger"  # 赤色
            status_text = "失敗"

        # メッセージ本文の構築
        text = f"{icon} {result.process_name} - {status_text}"

        # 詳細情報の構築
        fields = []

        if result.file_name:
            fields.append({"title": "ファイル名", "value": result.file_name, "short": True})

        if result.processing_time:
            fields.append({"title": "処理時間", "value": f"{result.processing_time:.1f}秒", "short": True})

        if result.timestamp:
            fields.append({"title": "実行時刻", "value": result.timestamp, "short": True})

        if not result.success and result.error_message:
            fields.append({"title": "エラー内容", "value": result.error_message, "short": False})

        # Slack Attachment形式でメッセージを構築
        payload = {"text": text, "attachments": [{"color": color, "fields": fields, "footer": "ショート動画設計図生成システム", "ts": int(time.time())}]}

        return payload

    def _call_webhook_api(self, payload: Dict[str, Any], max_retries: int = 3) -> None:
        """リトライ機能付きWebHook API呼び出し

        Args:
            payload: WebHook APIに送信するペイロード
            max_retries: 最大リトライ回数

        Raises:
            SlackWebHookError: WebHook API呼び出しに失敗した場合
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                response = requests.post(self.webhook_url, json=payload, timeout=self.timeout, headers={"Content-Type": "application/json"})

                # Slackは成功時に"ok"を返す
                if response.status_code == 200 and response.text == "ok":
                    return

                # エラーレスポンスの処理
                if response.status_code == 429:  # Rate Limit
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < max_retries - 1:
                        time.sleep(retry_after)
                        continue

                raise SlackWebHookError(f"Slack WebHook API呼び出しに失敗しました: {response.status_code} - {response.text}", status_code=response.status_code)

            except requests.exceptions.RequestException as e:
                last_exception = e

                if attempt < max_retries - 1:
                    time.sleep(2**attempt)  # 指数バックオフ
                    continue

        raise SlackWebHookError(f"Slack WebHook API呼び出しが{max_retries}回失敗しました: {str(last_exception)}")

    def _validate_message(self, message: str) -> None:
        """メッセージの妥当性チェック

        Args:
            message: 検証するメッセージ

        Raises:
            MessageValidationError: メッセージ内容が無効な場合
        """
        if not message or not message.strip():
            raise MessageValidationError("メッセージが空です")

        # Slackのメッセージ長制限（40,000文字）
        if len(message) > 40000:
            raise MessageValidationError("メッセージが長すぎます（40,000文字以内）")

    def _validate_process_result(self, result: ProcessResult) -> None:
        """ProcessResultの妥当性チェック

        Args:
            result: 検証する処理結果情報

        Raises:
            MessageValidationError: 処理結果情報が無効な場合
        """
        if not result.process_name or not result.process_name.strip():
            raise MessageValidationError("プロセス名が指定されていません", "process_name")

        if result.processing_time is not None and result.processing_time < 0:
            raise MessageValidationError("処理時間は0以上である必要があります", "processing_time")
