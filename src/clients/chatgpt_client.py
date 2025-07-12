"""ChatGPT APIクライアントモジュール"""

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..builders.prompt_builder import PromptBuilder

from openai import OpenAI

from ..models.hooks import DetailedScript, HookItem
from ..models.transcription import TranscriptionSegment


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
    """ChatGPT APIクライアント（2段階処理対応版）

    プロンプトからショート動画企画書をJSON形式で生成します。
    2段階処理（フック抽出→詳細台本作成）に対応し、並列処理も可能です。
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

    def extract_hooks(self, prompt: str) -> list[HookItem]:
        """フック抽出API呼び出し

        Args:
            prompt: フック抽出用プロンプト

        Returns:
            10個のHookItemのリスト

        Raises:
            ChatGPTAPIError: API呼び出しに失敗した場合
            JSONParseError: レスポンスのJSON解析に失敗した場合
            ValidationError: レスポンス内容が期待する形式でない場合

        """
        self._validate_prompt(prompt)

        raw_response = self._call_chatgpt_api(prompt)
        json_data = self._parse_json_response(raw_response)
        self._validate_hooks_response_structure(json_data)

        return self._convert_to_hook_items(json_data)

    def generate_detailed_script(self, prompt: str, hook_item: HookItem) -> DetailedScript:
        """詳細台本生成API呼び出し

        Args:
            prompt: 詳細台本生成用プロンプト
            hook_item: 対応するフックアイテム

        Returns:
            単一の詳細台本

        Note:
            詳細台本生成は台本形式のテキストを出力するため、
            JSONパースは行わずに生テキストとして処理する

        """
        self._validate_prompt(prompt)

        raw_response = self._call_chatgpt_api(prompt)

        # 台本は構造化されたJSONではなく、台本形式のテキストとして返される
        # 例: 【台本構成】[00:00–00:06] ナレーション＋テロップ...
        duration = self._extract_duration_from_script(raw_response)

        return DetailedScript(
            hook_item=hook_item,
            script_content=raw_response,
            duration_seconds=duration,
            segments_used=[],  # 後で設定
        )

    def generate_detailed_scripts_parallel(
        self, hook_items: list[HookItem], segments: list[TranscriptionSegment], prompt_builder: "PromptBuilder"
    ) -> list[DetailedScript]:
        """10個のフックに対して並列で詳細台本を生成

        Args:
            hook_items: フックアイテムのリスト
            segments: 文字起こしセグメント
            prompt_builder: プロンプトビルダー

        Returns:
            詳細台本のリスト

        """
        detailed_scripts = []

        # 並列処理（最大5並列）
        with ThreadPoolExecutor(max_workers=5) as executor:
            # 各フックに対してタスクを投入
            future_to_hook = {}
            for hook_item in hook_items:
                prompt = prompt_builder.build_script_prompt(hook_item, segments)
                future = executor.submit(self.generate_detailed_script, prompt, hook_item)
                future_to_hook[future] = hook_item

            # 結果を収集
            for future in as_completed(future_to_hook):
                hook_item = future_to_hook[future]
                try:
                    script = future.result()
                    # セグメント情報を設定
                    script.segments_used = segments  # 全セグメントを設定
                    detailed_scripts.append(script)
                except Exception as e:
                    # 個別の失敗は警告として記録し、処理を継続
                    print(f"フック '{hook_item.summary}' の台本生成に失敗: {e}")

        return detailed_scripts

    def _extract_duration_from_script(self, script_content: str) -> int:
        """台本内容から想定時間を抽出

        Args:
            script_content: 台本テキスト

        Returns:
            想定時間（秒）、抽出できない場合は60秒

        """
        # [00:54–01:00] のような時間表記を探す
        time_pattern = r"\[(\d{2}):(\d{2})–(\d{2}):(\d{2})\]"
        matches = re.findall(time_pattern, script_content)

        if matches:
            # 最後の時間表記を取得
            last_match = matches[-1]
            end_minutes = int(last_match[2])
            end_seconds = int(last_match[3])
            total_seconds = end_minutes * 60 + end_seconds
            return total_seconds

        # デフォルトは60秒
        return 60

    def _validate_hooks_response_structure(self, data: dict[str, Any]) -> None:
        """フック抽出レスポンスJSONの構造検証"""
        if "items" not in data:
            raise ValidationError("レスポンスに'items'フィールドがありません")

        if not isinstance(data["items"], list):
            raise ValidationError("'items'フィールドがリスト形式ではありません")

        if len(data["items"]) == 0:
            raise ValidationError("'items'が空です")

        required_fields = ["first_hook", "second_hook", "third_hook", "last_conclusion", "summary"]

        for i, item in enumerate(data["items"]):
            for field in required_fields:
                if field not in item:
                    raise ValidationError(
                        f"アイテム{i}に必須フィールド'{field}'がありません",
                        field_name=field,
                    )

    def _convert_to_hook_items(self, data: dict[str, Any]) -> list[HookItem]:
        """JSONデータをHookItemオブジェクトのリストに変換"""
        hook_items = []

        for item in data["items"]:
            hook_item = HookItem(
                first_hook=item["first_hook"],
                second_hook=item["second_hook"],
                third_hook=item["third_hook"],
                last_conclusion=item["last_conclusion"],
                summary=item["summary"],
            )
            hook_items.append(hook_item)

        return hook_items
