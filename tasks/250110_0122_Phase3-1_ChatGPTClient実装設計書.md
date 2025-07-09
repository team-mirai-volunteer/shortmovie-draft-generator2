# Phase3-1: ChatGPTClient実装設計書

## 概要

ショート動画設計図生成プロジェクトのPhase3-1として、ChatGPT APIとの通信を担当する`ChatGPTClient`クラスを実装します。
Phase2で実装した`PromptBuilder`が生成するプロンプトを受け取り、ChatGPT APIに送信して企画書データを取得する機能を提供します。

## 実装対象

### 1. ディレクトリ構造

```
src/
├── __init__.py
├── models/          # Phase1で実装済み
├── builders/        # Phase2で実装済み
└── clients/
    ├── __init__.py
    └── chatgpt_client.py    # 新規実装
```

### 2. ChatGPTClientクラスの設計

#### 2.1 基本仕様

```python
from typing import Dict, Any, Optional
import json
from openai import OpenAI
from ..models.draft import ShortVideoProposal, DraftResult
from ..models.transcription import TranscriptionResult

class ChatGPTClient:
    """ChatGPT APIクライアント

    PromptBuilderが生成したプロンプトをChatGPT APIに送信し、
    ショート動画企画書のJSON形式レスポンスを取得・解析します。

    Attributes:
        api_key: OpenAI APIキー
        model: 使用するChatGPTモデル（デフォルト: gpt-4）
        client: OpenAI APIクライアントインスタンス

    Example:
        >>> client = ChatGPTClient("your-api-key")
        >>> prompt = "企画書生成プロンプト..."
        >>> transcription = TranscriptionResult(...)
        >>> result = client.generate_draft(prompt, transcription)
        >>> print(f"生成された企画数: {len(result.proposals)}")
    """

    def __init__(self, api_key: str, model: str = "gpt-4") -> None:
        """ChatGPTClientを初期化

        Args:
            api_key: OpenAI APIキー
            model: 使用するChatGPTモデル

        Raises:
            ValueError: APIキーが無効な場合
        """

    def generate_draft(self, prompt: str, original_transcription: TranscriptionResult) -> DraftResult:
        """プロンプトから企画書を生成

        Args:
            prompt: PromptBuilderが生成したプロンプト
            original_transcription: 元の文字起こし結果

        Returns:
            企画書生成結果（DraftResult）

        Raises:
            ChatGPTAPIError: API呼び出しに失敗した場合
            JSONParseError: レスポンスのJSON解析に失敗した場合
            ValidationError: レスポンス内容が期待する形式でない場合
        """
```

#### 2.2 期待するChatGPTレスポンス形式

Phase2のPromptBuilderが指定する形式に基づいて、以下のJSON構造を期待します：

```json
{
  "items": [
    {
      "first_impact": "最初の2秒に含まれる、興味を惹くフレーズ",
      "last_conclusion": "動画の最後に来る結論。関心して終われる学び、共感できる内容、もしくは笑えるオチなど",
      "summary": "動画の主題。〇〇は〇〇なので〇〇である。ような端的な形式",
      "time_start": "開始時刻(hh:mm:ss)",
      "time_end": "終了時刻(hh:mm:ss)",
      "title": "魅力的なタイトル（30文字以内）",
      "caption": "SNS投稿用キャプション（100文字以内、ハッシュタグ含む）",
      "key_points": [
        "重要なポイント1",
        "重要なポイント2",
        "重要なポイント3"
      ]
    }
  ]
}
```

### 3. データ構造の拡張

#### 3.1 ShortVideoProposalクラスの更新

Phase2の設計に基づいて、既存の`ShortVideoProposal`クラスに新しいフィールドを追加します：

```python
@dataclass
class ShortVideoProposal:
    """ショート動画の企画提案（拡張版）"""
    title: str                    # 動画タイトル
    start_time: float            # 切り抜き開始時刻（秒）
    end_time: float              # 切り抜き終了時刻（秒）
    caption: str                 # キャプション
    key_points: List[str]        # キーポイントのリスト
    first_impact: str            # 冒頭2秒のインパクトフレーズ（新規追加）
    last_conclusion: str         # 最後の結論・オチ（新規追加）
    summary: str                 # 動画の主題（新規追加）
```

### 4. エラーハンドリング設計

#### 4.1 カスタム例外クラス

```python
class ChatGPTClientError(Exception):
    """ChatGPTClient関連のベース例外"""
    pass

class ChatGPTAPIError(ChatGPTClientError):
    """ChatGPT API呼び出しエラー"""
    def __init__(self, message: str, status_code: Optional[int] = None, retry_after: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after

class JSONParseError(ChatGPTClientError):
    """JSONレスポンス解析エラー"""
    def __init__(self, message: str, raw_response: str):
        super().__init__(message)
        self.raw_response = raw_response

class ValidationError(ChatGPTClientError):
    """レスポンス内容検証エラー"""
    def __init__(self, message: str, field_name: Optional[str] = None):
        super().__init__(message)
        self.field_name = field_name
```

#### 4.2 リトライ機能

```python
def _call_api_with_retry(self, prompt: str, max_retries: int = 3) -> str:
    """リトライ機能付きAPI呼び出し

    Args:
        prompt: 送信するプロンプト
        max_retries: 最大リトライ回数

    Returns:
        ChatGPTからのレスポンステキスト

    Raises:
        ChatGPTAPIError: 最大リトライ回数を超えた場合
    """
```

### 5. 実装仕様

#### 5.1 src/clients/__init__.py

```python
"""APIクライアントパッケージ"""

from .chatgpt_client import ChatGPTClient, ChatGPTClientError, ChatGPTAPIError, JSONParseError, ValidationError

__all__ = [
    "ChatGPTClient",
    "ChatGPTClientError",
    "ChatGPTAPIError",
    "JSONParseError",
    "ValidationError",
]
```

#### 5.2 src/clients/chatgpt_client.py

```python
"""ChatGPT APIクライアントモジュール"""

import json
import time
from typing import Dict, Any, List, Optional
from openai import OpenAI
from openai.types.chat import ChatCompletion

from ..models.draft import ShortVideoProposal, DraftResult
from ..models.transcription import TranscriptionResult


class ChatGPTClientError(Exception):
    """ChatGPTClient関連のベース例外"""
    pass


class ChatGPTAPIError(ChatGPTClientError):
    """ChatGPT API呼び出しエラー"""
    def __init__(self, message: str, status_code: Optional[int] = None, retry_after: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


class JSONParseError(ChatGPTClientError):
    """JSONレスポンス解析エラー"""
    def __init__(self, message: str, raw_response: str):
        super().__init__(message)
        self.raw_response = raw_response


class ValidationError(ChatGPTClientError):
    """レスポンス内容検証エラー"""
    def __init__(self, message: str, field_name: Optional[str] = None):
        super().__init__(message)
        self.field_name = field_name


class ChatGPTClient:
    """ChatGPT APIクライアント

    PromptBuilderが生成したプロンプトをChatGPT APIに送信し、
    ショート動画企画書のJSON形式レスポンスを取得・解析します。

    Example:
        >>> client = ChatGPTClient("your-api-key")
        >>> prompt = "企画書生成プロンプト..."
        >>> transcription = TranscriptionResult(...)
        >>> result = client.generate_draft(prompt, transcription)
        >>> print(f"生成された企画数: {len(result.proposals)}")
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

    def generate_draft(self, prompt: str, original_transcription: TranscriptionResult) -> DraftResult:
        """プロンプトから企画書を生成

        Args:
            prompt: PromptBuilderが生成したプロンプト
            original_transcription: 元の文字起こし結果

        Returns:
            企画書生成結果（DraftResult）

        Raises:
            ChatGPTAPIError: API呼び出しに失敗した場合
            JSONParseError: レスポンスのJSON解析に失敗した場合
            ValidationError: レスポンス内容が期待する形式でない場合
        """
        # API呼び出し（リトライ機能付き）
        response_text = self._call_api_with_retry(prompt)

        # JSONレスポンス解析
        response_data = self._parse_json_response(response_text)

        # データ検証
        self._validate_response_data(response_data)

        # ShortVideoProposalオブジェクトに変換
        proposals = self._convert_to_proposals(response_data["items"])

        return DraftResult(
            proposals=proposals,
            original_transcription=original_transcription
        )

    def _call_api_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """リトライ機能付きAPI呼び出し"""
        last_exception = None

        for attempt in range(max_retries):
            try:
                response: ChatCompletion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )

                return response.choices[0].message.content or ""

            except Exception as e:
                last_exception = e

                # レート制限の場合は待機時間を設定
                if hasattr(e, 'status_code') and e.status_code == 429:
                    retry_after = getattr(e, 'retry_after', 60)
                    if attempt < max_retries - 1:
                        time.sleep(retry_after)
                        continue

                # その他のエラーの場合は短時間待機
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数バックオフ

        # 最大リトライ回数を超えた場合
        raise ChatGPTAPIError(
            f"API呼び出しが{max_retries}回失敗しました: {str(last_exception)}"
        )

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """JSONレスポンス解析"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            raise JSONParseError(
                f"JSONの解析に失敗しました: {str(e)}",
                raw_response=response_text
            )

    def _validate_response_data(self, data: Dict[str, Any]) -> None:
        """レスポンスデータの検証"""
        if "items" not in data:
            raise ValidationError("レスポンスに'items'フィールドがありません")

        if not isinstance(data["items"], list):
            raise ValidationError("'items'フィールドがリスト形式ではありません")

        if len(data["items"]) != 5:
            raise ValidationError(f"企画提案は5個である必要があります（実際: {len(data['items'])}個）")

        required_fields = [
            "first_impact", "last_conclusion", "summary",
            "time_start", "time_end", "title", "caption", "key_points"
        ]

        for i, item in enumerate(data["items"]):
            for field in required_fields:
                if field not in item:
                    raise ValidationError(
                        f"企画提案{i+1}に必須フィールド'{field}'がありません",
                        field_name=field
                    )

    def _convert_to_proposals(self, items: List[Dict[str, Any]]) -> List[ShortVideoProposal]:
        """APIレスポンスをShortVideoProposalオブジェクトに変換"""
        proposals = []

        for item in items:
            # 時刻文字列を秒数に変換
            start_time = self._parse_time_to_seconds(item["time_start"])
            end_time = self._parse_time_to_seconds(item["time_end"])

            proposal = ShortVideoProposal(
                title=item["title"],
                start_time=start_time,
                end_time=end_time,
                caption=item["caption"],
                key_points=item["key_points"],
                first_impact=item["first_impact"],
                last_conclusion=item["last_conclusion"],
                summary=item["summary"]
            )
            proposals.append(proposal)

        return proposals

    def _parse_time_to_seconds(self, time_str: str) -> float:
        """hh:mm:ss形式の時刻文字列を秒数に変換"""
        try:
            parts = time_str.split(":")
            if len(parts) != 3:
                raise ValueError(f"時刻形式が不正です: {time_str}")

            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])

            return float(hours * 3600 + minutes * 60 + seconds)

        except (ValueError, IndexError) as e:
            raise ValidationError(f"時刻の解析に失敗しました: {time_str} - {str(e)}")
```

### 6. テスト設計

#### 6.1 テスト構造

```
tests/
├── __init__.py
├── test_models/     # Phase1で実装済み
├── test_builders/   # Phase2で実装済み
└── test_clients/
    ├── __init__.py
    └── test_chatgpt_client.py    # 新規実装
```

#### 6.2 テスト内容

##### 6.2.1 基本機能テスト

```python
class TestChatGPTClient:
    """ChatGPTClientの基本機能テスト"""

    def test_instance_creation(self):
        """インスタンス生成テスト"""
        client = ChatGPTClient("test-api-key")
        assert client.api_key == "test-api-key"
        assert client.model == "gpt-4"

    def test_instance_creation_with_custom_model(self):
        """カスタムモデル指定でのインスタンス生成テスト"""
        client = ChatGPTClient("test-api-key", model="gpt-3.5-turbo")
        assert client.model == "gpt-3.5-turbo"

    def test_invalid_api_key(self):
        """無効なAPIキーでのエラーテスト"""
        with pytest.raises(ValueError, match="APIキーが指定されていません"):
            ChatGPTClient("")
```

##### 6.2.2 JSON解析テスト

```python
class TestJSONParsing:
    """JSON解析機能テスト"""

    def test_parse_valid_json(self):
        """正常なJSON解析テスト"""
        client = ChatGPTClient("test-api-key")
        valid_json = '{"items": []}'
        result = client._parse_json_response(valid_json)
        assert result == {"items": []}

    def test_parse_invalid_json(self):
        """不正なJSON解析エラーテスト"""
        client = ChatGPTClient("test-api-key")
        invalid_json = '{"items": [}'  # 不正なJSON

        with pytest.raises(JSONParseError) as exc_info:
            client._parse_json_response(invalid_json)

        assert "JSONの解析に失敗しました" in str(exc_info.value)
        assert exc_info.value.raw_response == invalid_json
```

##### 6.2.3 時刻変換テスト

```python
class TestTimeConversion:
    """時刻変換機能テスト"""

    def test_parse_time_to_seconds_basic(self):
        """基本的な時刻変換テスト"""
        client = ChatGPTClient("test-api-key")

        assert client._parse_time_to_seconds("00:00:00") == 0.0
        assert client._parse_time_to_seconds("00:01:05") == 65.0
        assert client._parse_time_to_seconds("01:01:01") == 3661.0

    def test_parse_time_invalid_format(self):
        """不正な時刻形式のエラーテスト"""
        client = ChatGPTClient("test-api-key")

        with pytest.raises(ValidationError, match="時刻の解析に失敗しました"):
            client._parse_time_to_seconds("invalid-time")
```

#### 6.3 Integration Test設計

##### 6.3.1 実際のAPI呼び出しテスト

```python
@pytest.mark.integration
class TestChatGPTClientIntegration:
    """ChatGPTClientのIntegration Test"""

    @pytest.fixture
    def client(self):
        """テスト用クライアント"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEYが設定されていません")
        return ChatGPTClient(api_key)

    @pytest.fixture
    def sample_prompt(self):
        """テスト用プロンプト"""
        from src.builders.prompt_builder import PromptBuilder
        from src.models.transcription import TranscriptionSegment, TranscriptionResult

        segments = [
            TranscriptionSegment(0.0, 30.0, "今日は面白い話をします"),
            TranscriptionSegment(30.0, 60.0, "この方法を使えば必ず成功します"),
        ]
        transcription = TranscriptionResult(segments, "今日は面白い話をします。この方法を使えば必ず成功します。")

        builder = PromptBuilder()
        return builder.build_draft_prompt(transcription)

    def test_generate_draft_with_real_api(self, client, sample_prompt):
        """実際のAPI呼び出しでの企画書生成テスト"""
        from src.models.transcription import TranscriptionSegment, TranscriptionResult

        transcription = TranscriptionResult(
            segments=[TranscriptionSegment(0.0, 60.0, "テスト内容")],
            full_text="テスト内容"
        )

        result = client.generate_draft(sample_prompt, transcription)

        # 基本的な検証
        assert isinstance(result, DraftResult)
        assert len(result.proposals) == 5
        assert result.original_transcription == transcription

        # 各企画提案の検証
        for proposal in result.proposals:
            assert isinstance(proposal.title, str)
            assert len(proposal.title) <= 30
            assert isinstance(proposal.caption, str)
            assert len(proposal.caption) <= 100
            assert isinstance(proposal.key_points, list)
            assert len(proposal.key_points) >= 1
            assert proposal.start_time < proposal.end_time
            assert proposal.end_time - proposal.start_time <= 60  # 1分以内
```

### 7. 実装手順

#### Phase 3-1.1: 基本クラス実装
1. `src/clients/`ディレクトリの作成
2. カスタム例外クラスの実装
3. `ChatGPTClient`クラスの基本構造実装
4. `__init__.py`の実装

#### Phase 3-1.2: API通信機能実装
1. OpenAI APIクライアントの初期化
2. `_call_api_with_retry`メソッドの実装
3. リトライ機能とエラーハンドリングの実装

#### Phase 3-1.3: データ変換機能実装
1. JSON解析機能の実装
2. レスポンス検証機能の実装
3. 時刻変換機能の実装
4. `ShortVideoProposal`オブジェクト変換機能の実装

#### Phase 3-1.4: テスト実装
1. `tests/test_clients/`ディレクトリの作成
2. 基本機能テストの実装
3. JSON解析・時刻変換テストの実装
4. Integration Testの実装

#### Phase 3-1.5: データ構造更新
1. `src/models/draft.py`の`ShortVideoProposal`クラス更新
2. 既存テストの更新
3. 型チェックとリンターチェック

### 8. 完了条件

#### 必須条件
- [ ] `ChatGPTClient`クラスが正しく実装されている
- [ ] 実際のChatGPT APIとの通信が成功する
- [ ] JSON形式のレスポンスが正しく解析される
- [ ] 5個の企画提案が`ShortVideoProposal`オブジェクトに変換される
- [ ] エラーハンドリングとリトライ機能が動作する
- [ ] `mypy`による型チェックが通る
- [ ] 基本的なテストが全て通る
- [ ] Integration Testが通る（`INTEGRATION_TEST=true`環境）
- [ ] docstringが適切に記載されている

#### 品質条件
- [ ] コードが`black`でフォーマットされている
- [ ] `flake8`のリンターチェックが通る
- [ ] テストカバレッジが90%以上
- [ ] 実際のAPI呼び出しでの動作確認完了
- [ ] レスポンス品質の手動確認完了

### 9. 手動テスト項目

#### 9.1 API連携確認
1. **正常系**: 実際のプロンプトでChatGPT APIを呼び出し、期待する形式のレスポンスが返ってくる
2. **エラー系**: 不正なAPIキー、ネットワークエラー、レート制限での適切なエラーハンドリング
3. **リトライ機能**: 一時的な障害からの自動復旧
4. **レスポンス品質**: 生成される企画提案の内容が実用的

#### 9.2 データ変換確認
1. **時刻変換**: hh:mm:ss形式から秒数への正確な変換
2. **JSON解析**: 様々なレスポンス形式での堅牢な解析
3. **データ検証**: 不正なレスポンスでの適切なエラー検出
4. **オブジェクト変換**: `ShortVideoProposal`への正確な変換

### 10. 次フェーズへの引き継ぎ事項

#### Phase3-2（WhisperClient実装）で必要となる情報
- `ChatGPTClient`のエラーハンドリングパターン
- API呼び出しのリトライ機能実装方法
- Integration Testの設計パターン
- カスタム例外クラスの設計方針

#### Phase4（DraftGenerator実装）で必要となる情報
- `ChatGPTClient`の使用方法とインターフェース
- `DraftResult`オブジェクトの生成方法
- エラーハンドリングの統合方法
- 拡張された`ShortVideoProposal`の構造

### 11. 注意事項

#### 設計原則
- **堅牢性**: API障害やネットワークエラーに対する適切な対応
- **拡張性**: 将来的なChatGPTモデルの変更に対応
- **テスタビリティ**: 各機能が独立してテスト可能
- **実用性**: 実際のショート動画制作に役立つ品質

#### 実装時の注意点
- OpenAI APIの最新仕様に準拠
- レート制限を考慮したリトライ機能
- JSON解析の堅牢性を重視
- 時刻変換の精度を確保
- エラーメッセージは日本語で分かりやすく

この設計書に基づいて実装を進めることで、実用的で堅牢なChatGPT API連携機能を構築できます。
