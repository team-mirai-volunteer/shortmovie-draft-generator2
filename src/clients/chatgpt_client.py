"""ChatGPT APIクライアントモジュール"""

import json
import time
from typing import Any

from openai import OpenAI

from ..models.draft import ShortVideoProposal


class ChatGPTClientError(Exception):
    """ChatGPTClient関連のベース例外"""


class ChatGPTAPIError(ChatGPTClientError):
    """ChatGPT API呼び出しエラー"""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        retry_after: int | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


class JSONParseError(ChatGPTClientError):
    """JSON解析エラー"""

    def __init__(self, message: str, raw_response: str):
        super().__init__(message)
        self.raw_response = raw_response


class ValidationError(ChatGPTClientError):
    """レスポンス内容検証エラー"""

    def __init__(self, message: str, field_name: str | None = None):
        super().__init__(message)
        self.field_name = field_name


class ChatGPTClient:
    """ChatGPT APIクライアント

    プロンプトからショート動画企画書をJSON形式で生成します。
    レート制限やエラーハンドリングに対応し、構造化されたレスポンスを返します。

    Example:
        >>> client = ChatGPTClient("your-api-key")
        >>> response = client.generate_draft(prompt)
        >>> print(f"生成された企画数: {len(response)}")
        生成された企画数: 5

    """

    def __init__(self, api_key: str, model: str = "gpt-4") -> None:
        """ChatGPTClientを初期化

        Args:
            api_key: OpenAI APIキー
            model: 使用するChatGPTモデル

        Raises:
            ValueError: APIキーが無効な場合

        """
        if not api_key or not api_key.strip():
            raise ValueError("APIキーが指定されていません")

        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=api_key)

    def generate_draft(self, prompt: str) -> list[ShortVideoProposal]:
        """企画書生成用プロンプトからJSON形式の企画書を生成

        Args:
            prompt: ChatGPTに送信するプロンプト

        Returns:
            生成されたショート動画企画のリスト

        Raises:
            ChatGPTAPIError: API呼び出しに失敗した場合
            JSONParseError: レスポンスのJSON解析に失敗した場合
            ValidationError: レスポンス内容が期待する形式でない場合

        """
        self._validate_prompt(prompt)

        raw_response = self._call_chatgpt_api(prompt)
        json_data = self._parse_json_response(raw_response)
        self._validate_response_structure(json_data)

        return self._convert_to_proposals(json_data)

    def _validate_prompt(self, prompt: str) -> None:
        """プロンプトの妥当性チェック

        Args:
            prompt: 検証するプロンプト

        Raises:
            ValueError: プロンプトが無効な場合

        """
        if not prompt or not prompt.strip():
            raise ValueError("プロンプトが空です")

        if len(prompt) > 100000:
            raise ValueError("プロンプトが長すぎます（100,000文字以内）")

    def _call_chatgpt_api(self, prompt: str, max_retries: int = 3) -> str:
        """リトライ機能付きChatGPT API呼び出し

        Args:
            prompt: ChatGPTに送信するプロンプト
            max_retries: 最大リトライ回数

        Returns:
            ChatGPT APIからのレスポンステキスト

        Raises:
            ChatGPTAPIError: API呼び出しに失敗した場合

        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=4000,
                )

                content = response.choices[0].message.content
                if content is None:
                    raise ChatGPTAPIError("ChatGPTからの応答が空でした")
                return content

            except Exception as e:
                last_exception = e

                if hasattr(e, "status_code") and e.status_code == 429:
                    retry_after = getattr(e, "retry_after", 60)
                    if attempt < max_retries - 1:
                        time.sleep(retry_after)
                        continue

                if attempt < max_retries - 1:
                    time.sleep(2**attempt)

        raise ChatGPTAPIError(f"ChatGPT API呼び出しが{max_retries}回失敗しました: {last_exception!s}")

    def _parse_json_response(self, raw_response: str) -> dict[str, Any]:
        """レスポンステキストからJSONを抽出・解析

        Args:
            raw_response: ChatGPTからの生レスポンス

        Returns:
            解析されたJSONデータ

        Raises:
            JSONParseError: JSON解析に失敗した場合

        """
        try:
            cleaned_response = raw_response.strip()

            cleaned_response = cleaned_response.removeprefix("```json")
            cleaned_response = cleaned_response.removesuffix("```")

            cleaned_response = cleaned_response.strip()

            parsed_data = json.loads(cleaned_response)
            if not isinstance(parsed_data, dict):
                raise JSONParseError("レスポンスは辞書形式である必要があります", raw_response)
            return parsed_data

        except json.JSONDecodeError as e:
            raise JSONParseError(f"JSONの解析に失敗しました: {e!s}", raw_response) from e

    def _validate_response_structure(self, data: dict[str, Any]) -> None:
        """レスポンスJSONの構造検証

        Args:
            data: 検証するJSONデータ

        Raises:
            ValidationError: レスポンス構造が期待する形式でない場合

        """
        if "items" not in data:
            raise ValidationError("レスポンスに'items'フィールドがありません")

        if not isinstance(data["items"], list):
            raise ValidationError("'items'フィールドがリスト形式ではありません")

        if len(data["items"]) == 0:
            raise ValidationError("'items'が空です")

        required_fields = [
            "first_impact",
            "last_conclusion",
            "summary",
            "time_start",
            "time_end",
            "title",
            "caption",
            "key_points",
        ]

        for i, item in enumerate(data["items"]):
            for field in required_fields:
                if field not in item:
                    raise ValidationError(
                        f"アイテム{i}に必須フィールド'{field}'がありません",
                        field_name=field,
                    )

            if not isinstance(item["key_points"], list):
                raise ValidationError(f"アイテム{i}の'key_points'がリスト形式ではありません")

    def _convert_to_proposals(self, data: dict[str, Any]) -> list[ShortVideoProposal]:
        """JSONデータをShortVideoProposalオブジェクトのリストに変換

        Args:
            data: 変換するJSONデータ

        Returns:
            ShortVideoProposalオブジェクトのリスト

        """
        proposals = []

        for item in data["items"]:
            start_time = self._parse_time_to_seconds(item["time_start"])
            end_time = self._parse_time_to_seconds(item["time_end"])

            proposal = ShortVideoProposal(
                title=item["title"],
                start_time=start_time,
                end_time=end_time,
                caption=item["caption"],
                key_points=item["key_points"],
            )
            proposals.append(proposal)

        return proposals

    def _parse_time_to_seconds(self, time_str: str) -> float:
        """hh:mm:ss形式の時刻文字列を秒数に変換

        Args:
            time_str: hh:mm:ss形式の時刻文字列

        Returns:
            秒数（float）

        Raises:
            ValueError: 時刻形式が無効な場合

        """
        try:
            parts = time_str.split(":")
            if len(parts) != 3:
                raise ValueError(f"時刻形式が無効です: {time_str}")

            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])

            return hours * 3600 + minutes * 60 + seconds

        except (ValueError, IndexError) as e:
            raise ValueError(f"時刻の解析に失敗しました: {time_str} - {e!s}") from e
