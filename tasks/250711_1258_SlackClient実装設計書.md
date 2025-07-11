# SlackClient 実装設計書

## 概要

ショート動画設計図生成プロジェクトに Slack 通知機能を追加するため、WebHook 経由で Slack にメッセージを送信する SlackClient を実装します。

## 設計方針

### 基本方針

- 既存クライアント（ChatGPTClient、WhisperClient）の設計パターンに準拠
- WebHook URL を使用したシンプルな通知機能
- 処理完了通知（成功/失敗、処理時間、ファイル名など）に特化
- エラーハンドリングとリトライ機能を含む堅牢な実装

### 責務

- Slack WebHook API との通信
- 処理完了通知メッセージの送信
- 通信エラーのハンドリングとリトライ処理
- メッセージフォーマットの統一

## クラス設計

### 1. 例外クラス

```python
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
```

### 2. データクラス

```python
@dataclass
class ProcessResult:
    """処理結果を表すデータクラス"""
    success: bool
    process_name: str
    file_name: Optional[str] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    timestamp: Optional[str] = None
```

### 3. SlackClient クラス

```python
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

    def send_process_notification(self, result: ProcessResult) -> None:
        """処理完了通知を送信

        Args:
            result: 処理結果情報

        Raises:
            SlackWebHookError: WebHook API呼び出しに失敗した場合
            MessageValidationError: メッセージ内容が無効な場合
        """

    def send_message(self, message: str) -> None:
        """カスタムメッセージを送信

        Args:
            message: 送信するメッセージ

        Raises:
            SlackWebHookError: WebHook API呼び出しに失敗した場合
            MessageValidationError: メッセージ内容が無効な場合
        """
```

## 詳細設計

### 1. 初期化処理

```python
def __init__(self, webhook_url: str, timeout: int = 30) -> None:
    # WebHook URLの妥当性チェック
    if not webhook_url or not webhook_url.strip():
        raise ValueError("WebHook URLが指定されていません")

    if not webhook_url.startswith("https://hooks.slack.com/"):
        raise ValueError("無効なSlack WebHook URLです")

    self.webhook_url = webhook_url
    self.timeout = timeout
```

### 2. 処理完了通知メッセージ生成

```python
def _build_process_notification_message(self, result: ProcessResult) -> Dict[str, Any]:
    """処理完了通知メッセージを構築"""

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
        fields.append({
            "title": "ファイル名",
            "value": result.file_name,
            "short": True
        })

    if result.processing_time:
        fields.append({
            "title": "処理時間",
            "value": f"{result.processing_time:.1f}秒",
            "short": True
        })

    if result.timestamp:
        fields.append({
            "title": "実行時刻",
            "value": result.timestamp,
            "short": True
        })

    if not result.success and result.error_message:
        fields.append({
            "title": "エラー内容",
            "value": result.error_message,
            "short": False
        })

    # Slack Attachment形式でメッセージを構築
    payload = {
        "text": text,
        "attachments": [
            {
                "color": color,
                "fields": fields,
                "footer": "ショート動画設計図生成システム",
                "ts": int(time.time())
            }
        ]
    }

    return payload
```

### 3. WebHook API 呼び出し

```python
def _call_webhook_api(self, payload: Dict[str, Any], max_retries: int = 3) -> None:
    """リトライ機能付きWebHook API呼び出し"""

    import requests
    import json

    last_exception = None

    for attempt in range(max_retries):
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )

            # Slackは成功時に"ok"を返す
            if response.status_code == 200 and response.text == "ok":
                return

            # エラーレスポンスの処理
            if response.status_code == 429:  # Rate Limit
                retry_after = int(response.headers.get("Retry-After", 60))
                if attempt < max_retries - 1:
                    time.sleep(retry_after)
                    continue

            raise SlackWebHookError(
                f"Slack WebHook API呼び出しに失敗しました: {response.status_code} - {response.text}",
                status_code=response.status_code
            )

        except requests.exceptions.RequestException as e:
            last_exception = e

            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数バックオフ
                continue

    raise SlackWebHookError(
        f"Slack WebHook API呼び出しが{max_retries}回失敗しました: {str(last_exception)}"
    )
```

### 4. メッセージ検証

```python
def _validate_message(self, message: str) -> None:
    """メッセージの妥当性チェック"""

    if not message or not message.strip():
        raise MessageValidationError("メッセージが空です")

    # Slackのメッセージ長制限（40,000文字）
    if len(message) > 40000:
        raise MessageValidationError("メッセージが長すぎます（40,000文字以内）")

def _validate_process_result(self, result: ProcessResult) -> None:
    """ProcessResultの妥当性チェック"""

    if not result.process_name or not result.process_name.strip():
        raise MessageValidationError("プロセス名が指定されていません", "process_name")

    if result.processing_time is not None and result.processing_time < 0:
        raise MessageValidationError("処理時間は0以上である必要があります", "processing_time")
```

## ファイル構成

```
src/clients/slack_client.py
```

## 依存関係

### 新規追加

```toml
[tool.poetry.dependencies]
requests = "^2.31.0"
```

### インポート

```python
import json
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
import requests
```

## 使用例

### 1. 基本的な使用方法

```python
# 初期化
slack_client = SlackClient("https://hooks.slack.com/services/YOUR/WEBHOOK/URL")

# 成功通知
success_result = ProcessResult(
    success=True,
    process_name="ショート動画企画書生成",
    file_name="sample_video.mp4",
    processing_time=45.2,
    timestamp="2025-01-11 12:58:00"
)
slack_client.send_process_notification(success_result)

# 失敗通知
error_result = ProcessResult(
    success=False,
    process_name="ショート動画企画書生成",
    file_name="corrupted_video.mp4",
    error_message="動画ファイルの読み込みに失敗しました",
    timestamp="2025-01-11 13:05:00"
)
slack_client.send_process_notification(error_result)

# カスタムメッセージ
slack_client.send_message("システムメンテナンスを開始します")
```

### 2. DI コンテナでの使用

```python
class DIContainer:
    def __init__(self) -> None:
        # 環境変数からWebHook URLを取得
        slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")

        if slack_webhook_url:
            self._slack_client = SlackClient(slack_webhook_url)
        else:
            self._slack_client = None

    def get_slack_client(self) -> Optional[SlackClient]:
        return self._slack_client
```

## エラーハンドリング

### 1. 例外の種類

- `SlackWebHookError`: WebHook API 呼び出し失敗
- `MessageValidationError`: メッセージ内容の検証エラー
- `ValueError`: 初期化時の設定エラー

### 2. リトライ戦略

- 最大 3 回のリトライ
- 指数バックオフ（2^attempt 秒）
- Rate Limit 時は`Retry-After`ヘッダーに従う

### 3. タイムアウト処理

- デフォルト 30 秒の HTTP タイムアウト
- 初期化時に設定可能

## テスト設計

### 1. 単体テスト項目

- 正常系：メッセージ送信成功
- 異常系：無効な WebHook URL
- 異常系：空のメッセージ
- 異常系：長すぎるメッセージ
- 異常系：ネットワークエラー
- 異常系：Rate Limit

### 2. モック対象

- `requests.post`メソッド
- 時刻取得処理

## 将来拡張への考慮

### 1. メッセージフォーマット拡張

- リッチテキスト対応
- ボタンやアクション追加
- 画像添付機能

### 2. 通知レベル設定

- INFO、WARNING、ERROR レベル
- レベル別の通知先設定

### 3. バッチ送信機能

- 複数メッセージの一括送信
- 送信頻度制限機能

## セキュリティ考慮事項

### 1. WebHook URL 管理

- 環境変数での管理
- URL の妥当性チェック
- ログ出力時の URL マスキング

### 2. メッセージ内容

- 機密情報の除外
- メッセージ長制限
- 特殊文字のエスケープ

この設計により、既存のプロジェクト構造に適合し、堅牢で拡張性のある Slack 通知機能を提供できます。
