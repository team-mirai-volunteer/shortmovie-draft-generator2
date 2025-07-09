"""ChatGPT APIクライアントモジュール"""

import json
import os
import re
import time
from typing import Dict, Any, List

from openai import OpenAI

from ..models.draft import ShortVideoProposal, DraftResult
from ..models.transcription import TranscriptionResult
from ..builders.prompt_builder import PromptBuilder


class ChatGPTClientError(Exception):
    """ChatGPTクライアントの基底例外クラス"""

    pass


class ChatGPTAPIError(ChatGPTClientError):
    """ChatGPT API呼び出しエラー"""

    pass


class JSONParseError(ChatGPTClientError):
    """JSON解析エラー"""

    pass


class ValidationError(ChatGPTClientError):
    """データ検証エラー"""

    pass


class ChatGPTClient:
    """ChatGPT APIクライアント

    PromptBuilderが生成したプロンプトをChatGPT APIに送信し、
    ショート動画企画書のJSON形式レスポンスを取得・解析します。

    Attributes:
        api_key: OpenAI APIキー
        model: 使用するGPTモデル名
        max_retries: 最大リトライ回数
        retry_delay: リトライ間隔（秒）

    Example:
        >>> client = ChatGPTClient(api_key="your-api-key")
        >>> transcription = TranscriptionResult(segments, "テスト内容")
        >>> result = client.generate_draft(transcription)
        >>> print(len(result.proposals))
        5
    """

    def __init__(
        self,
        api_key: str = None,
        model: str = "gpt-4o-mini",
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """ChatGPTクライアントを初期化

        Args:
            api_key: OpenAI APIキー（未指定時は環境変数OPENAI_API_KEYを使用）
            model: 使用するGPTモデル名
            max_retries: 最大リトライ回数
            retry_delay: リトライ間隔（秒）

        Raises:
            ChatGPTClientError: APIキーが設定されていない場合
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ChatGPTClientError("OpenAI API key is required")

        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client = OpenAI(api_key=self.api_key)
        self._prompt_builder = PromptBuilder()

    def generate_draft(
        self, transcription: TranscriptionResult, additional_context: str = ""
    ) -> DraftResult:
        """文字起こし結果から企画書を生成

        Args:
            transcription: 文字起こし結果
            additional_context: 追加のコンテキスト情報

        Returns:
            生成された企画書結果

        Raises:
            ChatGPTAPIError: API呼び出しエラー
            JSONParseError: JSON解析エラー
            ValidationError: データ検証エラー
        """
        prompt = self._prompt_builder.build_draft_prompt(transcription)

        if additional_context:
            prompt += f"\n\n# 追加コンテキスト\n{additional_context}"

        messages = [
            {
                "role": "system",
                "content": "あなたはショート動画制作の専門家です。与えられた文字起こしから、魅力的なショート動画の企画を5個提案してください。",
            },
            {"role": "user", "content": prompt},
        ]

        response_text = self._make_api_call(messages)
        response_data = self._parse_json_response(response_text)
        proposals = self._validate_and_convert_proposals(response_data)

        return DraftResult(proposals=proposals, total_count=len(proposals))

    def generate_draft_from_prompt(
        self, prompt: str, additional_context: str = ""
    ) -> DraftResult:
        """プロンプトから企画書を生成

        Args:
            prompt: PromptBuilderが生成したプロンプト
            additional_context: 追加のコンテキスト情報

        Returns:
            生成された企画書結果

        Raises:
            ChatGPTAPIError: API呼び出しエラー
            JSONParseError: JSON解析エラー
            ValidationError: データ検証エラー
        """
        if additional_context:
            prompt += f"\n\n# 追加コンテキスト\n{additional_context}"

        messages = [
            {
                "role": "system",
                "content": "あなたはショート動画制作の専門家です。与えられた文字起こしから、魅力的なショート動画の企画を5個提案してください。",
            },
            {"role": "user", "content": prompt},
        ]

        response_text = self._make_api_call(messages)
        response_data = self._parse_json_response(response_text)
        proposals = self._validate_and_convert_proposals(response_data)

        return DraftResult(proposals=proposals, total_count=len(proposals))

    def _make_api_call(self, messages: List[Dict[str, str]]) -> str:
        """ChatGPT APIを呼び出し

        Args:
            messages: 送信するメッセージリスト

        Returns:
            APIレスポンステキスト

        Raises:
            ChatGPTAPIError: API呼び出しエラー
        """
        for attempt in range(self.max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=4000,
                )
                return response.choices[0].message.content

            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise ChatGPTAPIError(
                        f"ChatGPT API呼び出しに失敗しました: {str(e)}"
                    )

                time.sleep(self.retry_delay * (2**attempt))

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """ChatGPTレスポンスからJSONを解析

        Args:
            response_text: ChatGPTからのレスポンステキスト

        Returns:
            解析されたJSONデータ

        Raises:
            JSONParseError: JSON解析エラー
        """
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", response_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
        else:
            json_text = response_text.strip()

        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            raise JSONParseError(f"JSONの解析に失敗しました: {str(e)}")

    def _validate_and_convert_proposals(
        self, data: Dict[str, Any]
    ) -> List[ShortVideoProposal]:
        """レスポンスデータを検証し、ShortVideoProposalリストに変換

        Args:
            data: ChatGPTからのレスポンスデータ

        Returns:
            検証済みの企画提案リスト

        Raises:
            ValidationError: データ検証エラー
        """
        if "items" not in data:
            raise ValidationError("レスポンスに'items'フィールドが含まれていません")

        items = data["items"]
        if not isinstance(items, list):
            raise ValidationError("'items'フィールドはリストである必要があります")

        if len(items) != 5:
            raise ValidationError(
                f"企画提案は5個である必要があります（実際: {len(items)}個）"
            )

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

        proposals = []
        for i, item in enumerate(items):
            for field in required_fields:
                if field not in item:
                    raise ValidationError(
                        f"企画提案{i+1}に必須フィールド'{field}'がありません"
                    )

            try:
                start_time = self._convert_time_to_seconds(item["time_start"])
                end_time = self._convert_time_to_seconds(item["time_end"])

                if start_time >= end_time:
                    raise ValidationError(
                        f"企画提案{i+1}: 開始時刻は終了時刻より前である必要があります"
                    )

                proposal = ShortVideoProposal(
                    title=item["title"],
                    start_time=start_time,
                    end_time=end_time,
                    caption=item["caption"],
                    key_points=item["key_points"],
                    first_impact=item["first_impact"],
                    last_conclusion=item["last_conclusion"],
                    summary=item["summary"],
                )
                proposals.append(proposal)

            except (ValueError, KeyError) as e:
                raise ValidationError(f"企画提案{i+1}の変換に失敗しました: {str(e)}")

        return proposals

    def _convert_time_to_seconds(self, time_str: str) -> float:
        """時刻文字列を秒数に変換

        Args:
            time_str: 時刻文字列（hh:mm:ss、mm:ss、またはss形式）

        Returns:
            秒数

        Raises:
            ValidationError: 時刻フォーマットエラー
        """
        if not time_str or not time_str.strip():
            raise ValidationError(f"時刻フォーマットが無効です: {time_str}")

        try:
            parts = time_str.split(":")
            if len(parts) == 3:
                hours, minutes, seconds = map(int, parts)
                if (
                    minutes >= 60
                    or seconds >= 60
                    or hours < 0
                    or minutes < 0
                    or seconds < 0
                ):
                    raise ValueError("時刻の値が範囲外です")
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                minutes, seconds = map(int, parts)
                if minutes < 0 or seconds >= 60 or seconds < 0:
                    raise ValueError("時刻の値が範囲外です")
                return minutes * 60 + seconds
            elif len(parts) == 1:
                seconds = int(parts[0])
                if seconds < 0:
                    raise ValueError("時刻の値が範囲外です")
                return seconds
            else:
                raise ValueError("無効な時刻フォーマット")
        except ValueError:
            raise ValidationError(f"時刻フォーマットが無効です: {time_str}")
