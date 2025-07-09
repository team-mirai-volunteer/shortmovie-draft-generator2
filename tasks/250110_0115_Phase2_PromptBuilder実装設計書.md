# Phase2: PromptBuilder実装設計書

## 概要

ショート動画設計図生成プロジェクトのPhase2として、文字起こし結果からChatGPT用のプロンプトを生成する`PromptBuilder`クラスを実装します。
既存のプロトタイプを参考に、ショート動画制作のベストプラクティスに基づいた企画提案を5個生成するためのプロンプトを構築します。

## 実装対象

### 1. ディレクトリ構造

```
src/
├── __init__.py
├── models/          # Phase1で実装済み
└── builders/
    ├── __init__.py
    └── prompt_builder.py    # 新規実装
```

### 2. PromptBuilderクラスの設計

#### 2.1 基本仕様

```python
from typing import Dict, Any
from ..models.transcription import TranscriptionResult

class PromptBuilder:
    """ChatGPT用プロンプト生成クラス"""

    def build_draft_prompt(self, transcription: TranscriptionResult) -> str:
        """文字起こし結果からショート動画企画書生成用プロンプトを構築

        Args:
            transcription: 文字起こし結果

        Returns:
            ChatGPT APIに送信するプロンプト文字列
        """
```

#### 2.2 期待するChatGPT出力形式

既存プロトタイプを参考に、以下のJSON形式での回答を期待します：

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

**出力仕様**:
- 固定で5個の企画提案を生成
- 各提案は60秒以内の長さ
- ショート動画のベストプラクティスに基づいた構成

### 3. プロンプトテンプレートの設計

#### 3.1 改良されたプロンプト構造

```python
DRAFT_PROMPT_TEMPLATE = """
# 依頼内容
以下の動画の書き起こしテキストから、切り抜き動画として適切な部分の概要を抜き出してください。

- 動画の中で話している内容に肯定的な内容になるようにしてください。
- この動画から切り抜き動画を作って面白い動画を作りたいです。
- 切り抜き動画に向いている箇所を5個ピックアップしてください。
- 1分程度の尺になるようにしてください。

# 動画書き起こし

## 全体テキスト
{full_text}

## タイムスタンプ付きセグメント
{segments_text}

# 次の点をjson形式でアウトプットとして出してください

{{
  "items": [
    {{
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
    }},
    ...
  ]
}}

# ショート動画を作る主なポイントは以下の通りです。

## 冒頭2秒でインパクトを出す
* 冒頭の2秒はユーザーとの**最初の接点**であり、短い動画においては非常に大きい時間です。
* 基本的にフォロワー以外の動画が見られることが多いため、投稿者は**通りすがりの人**という認識を持つ必要があります。
* 通りすがりの人に丁寧な挨拶は不要であり、それよりも最初の数秒で「面白い」と思わせないと**スクロールされて消えていく**ため、**勝負にならない**とされています。
* バズった動画を分析した結果、伸びている動画の**9割はファーストビューを意識している**とのことです。
* 冒頭の2秒はYouTubeでいう**サムネイル**のようなもの

## 視聴時間をハックする（伸ばす）
* アルゴリズムの**7割が視聴時間**に関わっていると考えています。
* 個人的なデータとして、再生数と平均視聴時間にフル視聴率を掛け算した値は相関関係にあり、**すべては視聴時間に行き着く**とのことです。
* 「いいね！」やコメント率、シェア率よりも、**視聴時間の指標を重要視した方がバズる確率が高い**と述べています。
* 視聴時間を伸ばすためには、冒頭の2秒（サムネイル部分）以降の3秒目以降で**ユーザーが離脱しない内容**にする必要があります。
* ユーザーを**飽きさせない展開**を作り続けるのがコツです。
* トルコアイスの動画がお客を飽きさせない仕掛けを次々と繰り出すように、動画も5〜10秒程度で話を切り替えたり、色々なカットを使ったりする といった工夫が、視聴者を飽きさせないために有効だとされています。
* 終盤は視聴時間への寄与は少ないものの、最後に**共感や感動、オチ**などがあればユーザーの満足度が上がると考えられています。

JSON形式以外の出力は一切含めず、上記形式で正確に回答してください。
"""
```

#### 3.2 時刻フォーマット変換機能

```python
def _format_time_to_hms(self, seconds: float) -> str:
    """秒数をhh:mm:ss形式に変換"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def _format_segments(self, segments: List[TranscriptionSegment]) -> str:
    """セグメント情報を読みやすい形式にフォーマット"""
    formatted_lines = []
    for i, segment in enumerate(segments, 1):
        start_time = self._format_time_to_hms(segment.start_time)
        end_time = self._format_time_to_hms(segment.end_time)

        time_range = f"[{start_time} - {end_time}]"
        formatted_lines.append(f"{i:3d}. {time_range} {segment.text}")

    return "\n".join(formatted_lines)
```

### 4. データ構造の更新

#### 4.1 ShortVideoProposalの拡張

既存のデータ構造に新しいフィールドを追加：

```python
@dataclass
class ShortVideoProposal:
    """ショート動画の企画提案"""
    title: str                    # 動画タイトル
    start_time: float            # 切り抜き開始時刻（秒）
    end_time: float              # 切り抜き終了時刻（秒）
    caption: str                 # キャプション
    key_points: List[str]        # キーポイントのリスト
    first_impact: str            # 冒頭2秒のインパクトフレーズ
    last_conclusion: str         # 最後の結論・オチ
    summary: str                 # 動画の主題
```

### 5. 実装仕様

#### 5.1 src/builders/__init__.py

```python
"""プロンプト構築パッケージ"""

from .prompt_builder import PromptBuilder

__all__ = [
    "PromptBuilder",
]
```

#### 5.2 src/builders/prompt_builder.py

```python
"""ChatGPT用プロンプト生成モジュール"""

from typing import List
from ..models.transcription import TranscriptionResult, TranscriptionSegment


class PromptBuilder:
    """ChatGPT用プロンプト生成クラス

    文字起こし結果からショート動画企画書生成用のプロンプトを構築します。
    ショート動画のベストプラクティスに基づいた5個の企画提案を生成します。

    Example:
        >>> from src.models.transcription import TranscriptionResult, TranscriptionSegment
        >>> segments = [TranscriptionSegment(0.0, 10.0, "テスト内容")]
        >>> transcription = TranscriptionResult(segments, "テスト内容")
        >>> builder = PromptBuilder()
        >>> prompt = builder.build_draft_prompt(transcription)
        >>> print(len(prompt) > 0)
        True
    """

    # プロンプトテンプレート定数
    DRAFT_PROMPT_TEMPLATE = """..."""  # 上記テンプレート

    def build_draft_prompt(self, transcription: TranscriptionResult) -> str:
        """文字起こし結果からショート動画企画書生成用プロンプトを構築

        Args:
            transcription: 文字起こし結果

        Returns:
            ChatGPT APIに送信するプロンプト文字列

        Raises:
            ValueError: transcriptionが無効な場合
        """
        self._validate_transcription(transcription)

        segments_text = self._format_segments(transcription.segments)

        return self.DRAFT_PROMPT_TEMPLATE.format(
            full_text=transcription.full_text,
            segments_text=segments_text
        )

    def _format_time_to_hms(self, seconds: float) -> str:
        """秒数をhh:mm:ss形式に変換"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _format_segments(self, segments: List[TranscriptionSegment]) -> str:
        """セグメント情報を読みやすい形式にフォーマット"""
        formatted_lines = []
        for i, segment in enumerate(segments, 1):
            start_time = self._format_time_to_hms(segment.start_time)
            end_time = self._format_time_to_hms(segment.end_time)

            time_range = f"[{start_time} - {end_time}]"
            formatted_lines.append(f"{i:3d}. {time_range} {segment.text}")

        return "\n".join(formatted_lines)

    def _validate_transcription(self, transcription: TranscriptionResult) -> None:
        """文字起こし結果の妥当性をチェック"""
        if not transcription.segments:
            raise ValueError("セグメントが空です")
        if not transcription.full_text.strip():
            raise ValueError("全体テキストが空です")
```

### 6. テスト設計

#### 6.1 テスト構造

```
tests/
├── __init__.py
├── test_models/     # Phase1で実装済み
└── test_builders/
    ├── __init__.py
    └── test_prompt_builder.py    # 新規実装
```

#### 6.2 テスト内容

##### 6.2.1 基本機能テスト

```python
class TestPromptBuilder:
    """PromptBuilderの基本機能テスト"""

    def test_instance_creation(self):
        """インスタンス生成テスト"""
        builder = PromptBuilder()
        assert builder is not None

    def test_build_draft_prompt_basic(self):
        """基本的なプロンプト生成テスト"""
        segments = [TranscriptionSegment(0.0, 10.0, "テスト内容")]
        transcription = TranscriptionResult(segments, "テスト内容")
        builder = PromptBuilder()

        prompt = builder.build_draft_prompt(transcription)

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "テスト内容" in prompt
        assert "json形式" in prompt
        assert "first_impact" in prompt

    def test_prompt_contains_best_practices(self):
        """プロンプトにベストプラクティスが含まれているかテスト"""
        segments = [TranscriptionSegment(0.0, 10.0, "テスト")]
        transcription = TranscriptionResult(segments, "テスト")
        builder = PromptBuilder()

        prompt = builder.build_draft_prompt(transcription)

        assert "冒頭2秒でインパクト" in prompt
        assert "視聴時間をハック" in prompt
        assert "最初の接点" in prompt
```

##### 6.2.2 時刻フォーマット機能テスト

```python
class TestTimeFormatting:
    """時刻フォーマット機能テスト"""

    def test_format_time_to_hms_basic(self):
        """基本的な時刻フォーマットテスト"""
        builder = PromptBuilder()

        assert builder._format_time_to_hms(0.0) == "00:00:00"
        assert builder._format_time_to_hms(65.0) == "00:01:05"
        assert builder._format_time_to_hms(3661.0) == "01:01:01"

    def test_format_segments_with_time(self):
        """時刻付きセグメントフォーマットテスト"""
        segments = [
            TranscriptionSegment(0.0, 30.0, "最初の内容"),
            TranscriptionSegment(30.0, 90.0, "次の内容"),
        ]
        builder = PromptBuilder()

        formatted = builder._format_segments(segments)

        assert "[00:00:00 - 00:00:30]" in formatted
        assert "[00:00:30 - 00:01:30]" in formatted
        assert "最初の内容" in formatted
        assert "次の内容" in formatted
```

#### 6.3 サンプルデータ

##### 6.3.1 ショート動画向けテストデータ

```python
# ショート動画制作に適したテストデータ
SHORT_VIDEO_SEGMENTS = [
    TranscriptionSegment(0.0, 5.0, "皆さん、これ知ってました？実は..."),
    TranscriptionSegment(5.0, 15.0, "今日お話しするのは、誰も教えてくれない秘密の方法です"),
    TranscriptionSegment(15.0, 30.0, "まず最初のポイントは、タイミングが全てということ"),
    TranscriptionSegment(30.0, 45.0, "次に重要なのは、相手の心理を理解すること"),
    TranscriptionSegment(45.0, 60.0, "最後に、これを実践すれば必ず結果が出ます"),
]

SHORT_VIDEO_TRANSCRIPTION = TranscriptionResult(
    segments=SHORT_VIDEO_SEGMENTS,
    full_text="皆さん、これ知ってました？実は...今日お話しするのは、誰も教えてくれない秘密の方法です。まず最初のポイントは、タイミングが全てということ。次に重要なのは、相手の心理を理解すること。最後に、これを実践すれば必ず結果が出ます。"
)
```

### 7. 実装手順

#### Phase 2.1: 基本クラス実装
1. `src/builders/`ディレクトリの作成
2. `prompt_builder.py`の基本クラス実装
3. `build_draft_prompt`メソッドの実装
4. `__init__.py`の実装

#### Phase 2.2: プロンプトテンプレート実装
1. 改良されたプロンプトテンプレートの実装
2. 時刻フォーマット機能の実装
3. セグメントフォーマット機能の実装
4. バリデーション機能の実装

#### Phase 2.3: テスト実装
1. `tests/test_builders/`ディレクトリの作成
2. 基本機能テストの実装
3. 時刻フォーマット機能テストの実装
4. バリデーション機能テストの実装
5. ショート動画向けサンプルデータでの統合テスト

#### Phase 2.4: 品質チェック
1. `mypy`による型チェック
2. `flake8`によるコード品質チェック
3. `black`によるフォーマット適用
4. テスト実行とカバレッジ確認

### 8. 完了条件

#### 必須条件
- [ ] `PromptBuilder`クラスが正しく実装されている
- [ ] 文字起こし結果から適切なプロンプトが生成される
- [ ] 生成されたプロンプトにショート動画のベストプラクティスが含まれている
- [ ] 時刻フォーマットが正しく動作する
- [ ] `mypy`による型チェックが通る
- [ ] 基本的なテストが全て通る
- [ ] docstringが適切に記載されている

#### 品質条件
- [ ] コードが`black`でフォーマットされている
- [ ] `flake8`のリンターチェックが通る
- [ ] テストカバレッジが90%以上
- [ ] 実際の使用パターンでの動作確認完了
- [ ] プロンプトの品質が手動確認で妥当

### 9. 手動テスト項目

#### 9.1 プロンプト品質確認
1. **ベストプラクティス**: ショート動画制作の要点が含まれている
2. **具体性**: 「冒頭2秒」「視聴時間」などの具体的な指標が含まれている
3. **JSON形式指定**: 出力形式が正確に指定されている
4. **実用性**: 実際のショート動画制作に役立つ内容

#### 9.2 実際のChatGPT連携テスト（Phase3準備）
1. 生成されたプロンプトをChatGPTに送信
2. 期待するJSON形式で回答が返ってくるか確認
3. `first_impact`、`last_conclusion`、`summary`の品質確認
4. 時刻フォーマットの正確性確認

### 10. 次フェーズへの引き継ぎ事項

#### Phase3（API Clients実装）で必要となる情報
- `PromptBuilder`の使用方法とインターフェース
- 生成されるプロンプトの形式と内容
- ChatGPTからの期待する回答形式（拡張されたJSON構造）
- 時刻フォーマットの変換方法

#### Phase4（DraftGenerator実装）で必要となる情報
- 拡張されたJSON形式の企画提案データの構造
- `ShortVideoProposal`データクラスの更新要件
- `DraftResult`への変換方法

### 11. データ構造の更新要件

Phase1で実装した`ShortVideoProposal`クラスに以下のフィールドを追加する必要があります：

```python
# 追加フィールド
first_impact: str            # 冒頭2秒のインパクトフレーズ
last_conclusion: str         # 最後の結論・オチ
summary: str                 # 動画の主題
```

この更新はPhase3またはPhase4で実施します。

### 12. 注意事項

#### 設計原則
- **実用性**: 実際のショート動画制作に基づいた設計
- **ベストプラクティス**: 既存の成功事例を反映
- **拡張性**: 将来的なプロンプト改善に対応
- **テスタビリティ**: 各機能が独立してテスト可能

#### 実装時の注意点
- プロンプトテンプレートは定数として管理
- 時刻フォーマットはhh:mm:ss形式で統一
- エラーメッセージは日本語で分かりやすく
- ショート動画の特性を考慮した設計

この設計書に基づいて実装を進めることで、実用的で高品質なショート動画企画書生成機能を構築できます。
