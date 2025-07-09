# Phase3-2: WhisperClient実装設計書

## 概要

ショート動画設計図生成プロジェクトのPhase3-2として、Whisper APIとの通信を担当する`WhisperClient`クラスを実装します。
動画ファイルからの音声抽出（ffmpeg連携）、Whisper APIでの文字起こし、タイムスタンプ付きセグメントデータの生成を行います。

## 実装対象

### 1. ディレクトリ構造

```
src/
├── __init__.py
├── models/          # Phase1で実装済み
├── builders/        # Phase2で実装済み
└── clients/
    ├── __init__.py
    ├── chatgpt_client.py    # Phase3-1で実装済み
    └── whisper_client.py    # 新規実装
```

### 2. WhisperClientクラスの設計

#### 2.1 基本仕様

```python
from typing import Optional, Dict, Any
import os
import tempfile
from pathlib import Path
import ffmpeg
from openai import OpenAI
from ..models.transcription import TranscriptionSegment, TranscriptionResult

class WhisperClient:
    """Whisper APIクライアント

    動画ファイルから音声を抽出し、Whisper APIで文字起こしを実行します。
    タイムスタンプ付きのセグメント情報を含むTranscriptionResultを生成します。

    Attributes:
        api_key: OpenAI APIキー
        model: 使用するWhisperモデル（デフォルト: whisper-1）
        client: OpenAI APIクライアントインスタンス
        temp_dir: 一時ファイル保存ディレクトリ

    Example:
        >>> client = WhisperClient("your-api-key")
        >>> result = client.transcribe("input/video.mp4")
        >>> print(f"セグメント数: {len(result.segments)}")
        >>> print(f"全体テキスト: {result.full_text}")
    """

    def __init__(
        self,
        api_key: str,
        model: str = "whisper-1",
        temp_dir: Optional[str] = None
    ) -> None:
        """WhisperClientを初期化

        Args:
            api_key: OpenAI APIキー
            model: 使用するWhisperモデル
            temp_dir: 一時ファイル保存ディレクトリ（Noneの場合はシステムデフォルト）

        Raises:
            ValueError: APIキーが無効な場合
            OSError: 一時ディレクトリの作成に失敗した場合
        """

    def transcribe(self, video_path: str) -> TranscriptionResult:
        """動画ファイルから文字起こしを実行

        Args:
            video_path: 動画ファイルのパス

        Returns:
            文字起こし結果（TranscriptionResult）

        Raises:
            FileNotFoundError: 動画ファイルが存在しない場合
            AudioExtractionError: 音声抽出に失敗した場合
            WhisperAPIError: Whisper API呼び出しに失敗した場合
            ValidationError: レスポンス内容が期待する形式でない場合
        """
```

#### 2.2 音声抽出機能

```python
def _extract_audio(self, video_path: str) -> str:
    """動画ファイルから音声を抽出

    Args:
        video_path: 動画ファイルのパス

    Returns:
        抽出された音声ファイルのパス

    Raises:
        AudioExtractionError: 音声抽出に失敗した場合
    """
```

**音声抽出の仕様**:
- 入力: 動画ファイル（mp4, avi, mov, mkv等）
- 出力: WAV形式の音声ファイル（16kHz, モノラル）
- ffmpeg-pythonライブラリを使用
- 一時ディレクトリに音声ファイルを保存

#### 2.3 期待するWhisperレスポンス形式

Whisper APIから以下の形式のレスポンスを期待します：

```json
{
  "text": "全体の文字起こしテキスト",
  "segments": [
    {
      "id": 0,
      "seek": 0,
      "start": 0.0,
      "end": 3.5,
      "text": "こんにちは、今日は",
      "tokens": [50364, 50365, ...],
      "temperature": 0.0,
      "avg_logprob": -0.5,
      "compression_ratio": 1.2,
      "no_speech_prob": 0.1
    }
  ]
}
```

### 3. エラーハンドリング設計

#### 3.1 カスタム例外クラス

```python
class WhisperClientError(Exception):
    """WhisperClient関連のベース例外"""
    pass

class AudioExtractionError(WhisperClientError):
    """音声抽出エラー"""
    def __init__(self, message: str, video_path: str, ffmpeg_error: Optional[str] = None):
        super().__init__(message)
        self.video_path = video_path
        self.ffmpeg_error = ffmpeg_error

class WhisperAPIError(WhisperClientError):
    """Whisper API呼び出しエラー"""
    def __init__(self, message: str, status_code: Optional[int] = None, retry_after: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after

class ValidationError(WhisperClientError):
    """レスポンス内容検証エラー"""
    def __init__(self, message: str, field_name: Optional[str] = None):
        super().__init__(message)
        self.field_name = field_name
```

#### 3.2 ファイル管理機能

```python
def _cleanup_temp_files(self, *file_paths: str) -> None:
    """一時ファイルのクリーンアップ"""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass  # ログ出力のみ、エラーは無視

def _validate_video_file(self, video_path: str) -> None:
    """動画ファイルの妥当性チェック"""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"動画ファイルが見つかりません: {video_path}")

    # ファイルサイズチェック（25MB制限）
    file_size = os.path.getsize(video_path)
    max_size = 25 * 1024 * 1024  # 25MB
    if file_size > max_size:
        raise ValidationError(f"ファイルサイズが制限を超えています: {file_size / 1024 / 1024:.1f}MB > 25MB")
```

### 4. 実装仕様

#### 4.1 src/clients/whisper_client.py

```python
"""Whisper APIクライアントモジュール"""

import os
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import ffmpeg
from openai import OpenAI

from ..models.transcription import TranscriptionSegment, TranscriptionResult


class WhisperClientError(Exception):
    """WhisperClient関連のベース例外"""
    pass


class AudioExtractionError(WhisperClientError):
    """音声抽出エラー"""
    def __init__(self, message: str, video_path: str, ffmpeg_error: Optional[str] = None):
        super().__init__(message)
        self.video_path = video_path
        self.ffmpeg_error = ffmpeg_error


class WhisperAPIError(WhisperClientError):
    """Whisper API呼び出しエラー"""
    def __init__(self, message: str, status_code: Optional[int] = None, retry_after: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


class ValidationError(WhisperClientError):
    """レスポンス内容検証エラー"""
    def __init__(self, message: str, field_name: Optional[str] = None):
        super().__init__(message)
        self.field_name = field_name


class WhisperClient:
    """Whisper APIクライアント

    動画ファイルから音声を抽出し、Whisper APIで文字起こしを実行します。
    タイムスタンプ付きのセグメント情報を含むTranscriptionResultを生成します。

    Example:
        >>> client = WhisperClient("your-api-key")
        >>> result = client.transcribe("input/video.mp4")
        >>> print(f"セグメント数: {len(result.segments)}")
        セグメント数: 15
        >>> print(f"全体テキスト長: {len(result.full_text)}")
        全体テキスト長: 1250
    """

    def __init__(
        self,
        api_key: str,
        model: str = "whisper-1",
        temp_dir: Optional[str] = None
    ) -> None:
        """WhisperClientを初期化

        Args:
            api_key: OpenAI APIキー
            model: 使用するWhisperモデル
            temp_dir: 一時ファイル保存ディレクトリ

        Raises:
            ValueError: APIキーが無効な場合
            OSError: 一時ディレクトリの作成に失敗した場合
        """
        if not api_key or not api_key.strip():
            raise ValueError("APIキーが指定されていません")

        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=api_key)

        # 一時ディレクトリの設定
        if temp_dir:
            self.temp_dir = Path(temp_dir)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.temp_dir = Path(tempfile.gettempdir()) / "whisper_client"
            self.temp_dir.mkdir(parents=True, exist_ok=True)

    def transcribe(self, video_path: str) -> TranscriptionResult:
        """動画ファイルから文字起こしを実行

        Args:
            video_path: 動画ファイルのパス

        Returns:
            文字起こし結果（TranscriptionResult）

        Raises:
            FileNotFoundError: 動画ファイルが存在しない場合
            AudioExtractionError: 音声抽出に失敗した場合
            WhisperAPIError: Whisper API呼び出しに失敗した場合
            ValidationError: レスポンス内容が期待する形式でない場合
        """
        # 入力ファイルの検証
        self._validate_video_file(video_path)

        audio_path = None
        try:
            # 音声抽出
            audio_path = self._extract_audio(video_path)

            # Whisper API呼び出し
            response_data = self._call_whisper_api(audio_path)

            # レスポンス検証
            self._validate_response_data(response_data)

            # TranscriptionResultオブジェクトに変換
            return self._convert_to_transcription_result(response_data)

        finally:
            # 一時ファイルのクリーンアップ
            if audio_path:
                self._cleanup_temp_files(audio_path)

    def _validate_video_file(self, video_path: str) -> None:
        """動画ファイルの妥当性チェック"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"動画ファイルが見つかりません: {video_path}")

        # ファイルサイズチェック（25MB制限）
        file_size = os.path.getsize(video_path)
        max_size = 25 * 1024 * 1024  # 25MB
        if file_size > max_size:
            raise ValidationError(
                f"ファイルサイズが制限を超えています: {file_size / 1024 / 1024:.1f}MB > 25MB"
            )

        # ファイル拡張子チェック
        allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
        file_extension = Path(video_path).suffix.lower()
        if file_extension not in allowed_extensions:
            raise ValidationError(f"サポートされていないファイル形式です: {file_extension}")

    def _extract_audio(self, video_path: str) -> str:
        """動画ファイルから音声を抽出

        Args:
            video_path: 動画ファイルのパス

        Returns:
            抽出された音声ファイルのパス

        Raises:
            AudioExtractionError: 音声抽出に失敗した場合
        """
        try:
            # 出力ファイルパスの生成
            video_name = Path(video_path).stem
            audio_path = self.temp_dir / f"{video_name}_audio.wav"

            # ffmpegで音声抽出
            (
                ffmpeg
                .input(video_path)
                .output(
                    str(audio_path),
                    acodec='pcm_s16le',  # 16-bit PCM
                    ac=1,                # モノラル
                    ar=16000            # 16kHz サンプリングレート
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            # 出力ファイルの存在確認
            if not audio_path.exists():
                raise AudioExtractionError(
                    f"音声ファイルの生成に失敗しました: {audio_path}",
                    video_path
                )

            return str(audio_path)

        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if e.stderr else str(e)
            raise AudioExtractionError(
                f"ffmpegによる音声抽出に失敗しました: {error_message}",
                video_path,
                ffmpeg_error=error_message
            )
        except Exception as e:
            raise AudioExtractionError(
                f"音声抽出中に予期しないエラーが発生しました: {str(e)}",
                video_path
            )

    def _call_whisper_api(self, audio_path: str, max_retries: int = 3) -> Dict[str, Any]:
        """リトライ機能付きWhisper API呼び出し

        Args:
            audio_path: 音声ファイルのパス
            max_retries: 最大リトライ回数

        Returns:
            Whisper APIからのレスポンスデータ

        Raises:
            WhisperAPIError: API呼び出しに失敗した場合
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                with open(audio_path, 'rb') as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model=self.model,
                        file=audio_file,
                        response_format="verbose_json",
                        timestamp_granularities=["segment"]
                    )

                # レスポンスを辞書形式に変換
                return response.model_dump()

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
        raise WhisperAPIError(
            f"Whisper API呼び出しが{max_retries}回失敗しました: {str(last_exception)}"
        )

    def _validate_response_data(self, data: Dict[str, Any]) -> None:
        """レスポンスデータの検証

        Args:
            data: Whisper APIからのレスポンスデータ

        Raises:
            ValidationError: レスポンス内容が期待する形式でない場合
        """
        if "text" not in data:
            raise ValidationError("レスポンスに'text'フィールドがありません")

        if "segments" not in data:
            raise ValidationError("レスポンスに'segments'フィールドがありません")

        if not isinstance(data["segments"], list):
            raise ValidationError("'segments'フィールドがリスト形式ではありません")

        # 各セグメントの必須フィールドをチェック
        required_segment_fields = ["start", "end", "text"]
        for i, segment in enumerate(data["segments"]):
            for field in required_segment_fields:
                if field not in segment:
                    raise ValidationError(
                        f"セグメント{i}に必須フィールド'{field}'がありません",
                        field_name=field
                    )

    def _convert_to_transcription_result(self, data: Dict[str, Any]) -> TranscriptionResult:
        """APIレスポンスをTranscriptionResultオブジェクトに変換

        Args:
            data: Whisper APIからのレスポンスデータ

        Returns:
            TranscriptionResult オブジェクト
        """
        # セグメントデータの変換
        segments = []
        for segment_data in data["segments"]:
            segment = TranscriptionSegment(
                start_time=float(segment_data["start"]),
                end_time=float(segment_data["end"]),
                text=segment_data["text"].strip()
            )
            segments.append(segment)

        return TranscriptionResult(
            segments=segments,
            full_text=data["text"].strip()
        )

    def _cleanup_temp_files(self, *file_paths: str) -> None:
        """一時ファイルのクリーンアップ

        Args:
            *file_paths: クリーンアップ対象のファイルパス
        """
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except OSError:
                # ログ出力のみ、エラーは無視
                pass
```

### 5. テスト設計

#### 5.1 テスト構造

```
tests/
├── __init__.py
├── test_models/     # Phase1で実装済み
├── test_builders/   # Phase2で実装済み
├── test_clients/
│   ├── __init__.py
│   ├── test_chatgpt_client.py    # Phase3-1で実装済み
│   └── test_whisper_client.py    # 新規実装
└── fixtures/
    ├── sample_video.mp4          # テスト用動画ファイル
    ├── sample_audio.wav          # テスト用音声ファイル
    └── invalid_file.txt          # 不正ファイルテスト用
```

#### 5.2 テスト内容

##### 5.2.1 基本機能テスト

```python
class TestWhisperClient:
    """WhisperClientの基本機能テスト"""

    def test_instance_creation(self):
        """インスタンス生成テスト"""
        client = WhisperClient("test-api-key")
        assert client.api_key == "test-api-key"
        assert client.model == "whisper-1"
        assert client.temp_dir.exists()

    def test_instance_creation_with_custom_temp_dir(self, tmp_path):
        """カスタム一時ディレクトリでのインスタンス生成テスト"""
        custom_temp = tmp_path / "custom_temp"
        client = WhisperClient("test-api-key", temp_dir=str(custom_temp))
        assert client.temp_dir == custom_temp
        assert custom_temp.exists()

    def test_invalid_api_key(self):
        """無効なAPIキーでのエラーテスト"""
        with pytest.raises(ValueError, match="APIキーが指定されていません"):
            WhisperClient("")
```

##### 5.2.2 ファイル検証テスト

```python
class TestFileValidation:
    """ファイル検証機能テスト"""

    def test_validate_existing_video_file(self, sample_video_path):
        """存在する動画ファイルの検証テスト"""
        client = WhisperClient("test-api-key")
        # 例外が発生しないことを確認
        client._validate_video_file(sample_video_path)

    def test_validate_nonexistent_file(self):
        """存在しないファイルの検証エラーテスト"""
        client = WhisperClient("test-api-key")

        with pytest.raises(FileNotFoundError, match="動画ファイルが見つかりません"):
            client._validate_video_file("nonexistent.mp4")

    def test_validate_unsupported_file_format(self, tmp_path):
        """サポートされていないファイル形式のエラーテスト"""
        client = WhisperClient("test-api-key")

        # テキストファイルを作成
        text_file = tmp_path / "test.txt"
        text_file.write_text("test content")

        with pytest.raises(ValidationError, match="サポートされていないファイル形式"):
            client._validate_video_file(str(text_file))
```

##### 5.2.3 音声抽出テスト

```python
class TestAudioExtraction:
    """音声抽出機能テスト"""

    @pytest.fixture
    def client(self, tmp_path):
        """テスト用クライアント"""
        return WhisperClient("test-api-key", temp_dir=str(tmp_path))

    def test_extract_audio_success(self, client, sample_video_path):
        """正常な音声抽出テスト"""
        audio_path = client._extract_audio(sample_video_path)

        assert os.path.exists(audio_path)
        assert audio_path.endswith(".wav")

        # クリーンアップ
        client._cleanup_temp_files(audio_path)

    def test_extract_audio_invalid_video(self, client, tmp_path):
        """不正な動画ファイルでの音声抽出エラーテスト"""
        # 不正なファイルを作成
        invalid_file = tmp_path / "invalid.mp4"
        invalid_file.write_text("not a video file")

        with pytest.raises(AudioExtractionError, match="ffmpegによる音声抽出に失敗"):
            client._extract_audio(str(invalid_file))
```

#### 5.3 Integration Test設計

##### 5.3.1 実際のAPI呼び出しテスト

```python
@pytest.mark.integration
class TestWhisperClientIntegration:
    """WhisperClientのIntegration Test"""

    @pytest.fixture
    def client(self, tmp_path):
        """テスト用クライアント"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEYが設定されていません")
        return WhisperClient(api_key, temp_dir=str(tmp_path))

    @pytest.fixture
    def sample_video_path(self):
        """テスト用動画ファイル"""
        video_path = "tests/fixtures/sample_video.mp4"
        if not os.path.exists(video_path):
            pytest.skip("テスト用動画ファイルが存在しません")
        return video_path

    def test_transcribe_with_real_api(self, client, sample_video_path):
        """実際のAPI呼び出しでの文字起こしテスト"""
        result = client.transcribe(sample_video_path)

        # 基本的な検証
        assert isinstance(result, TranscriptionResult)
        assert isinstance(result.full_text, str)
        assert len(result.full_text) > 0
        assert isinstance(result.segments, list)
        assert len(result.segments) > 0

        # セグメントの検証
        for segment in result.segments:
            assert isinstance(segment, TranscriptionSegment)
            assert segment.start_time >= 0
            assert segment.end_time > segment.start_time
            assert isinstance(segment.text, str)
            assert len(segment.text.strip()) > 0

        # 時系列の整合性チェック
        for i in range(len(result.segments) - 1):
            current_segment = result.segments[i]
            next_segment = result.segments[i + 1]
            assert current_segment.end_time <= next_segment.start_time

    def test_transcribe_error_handling(self, client):
        """エラーハンドリングのテスト"""
        # 存在しないファイル
        with pytest.raises(FileNotFoundError):
            client.transcribe("nonexistent.mp4")

        # サポートされていないファイル形式
        with pytest.raises(ValidationError):
            client.transcribe("tests/fixtures/invalid_file.txt")
```

### 6. 依存関係とセットアップ

#### 6.1 必要なライブラリ

```toml
# pyproject.toml に追加
[tool.poetry.dependencies]
ffmpeg-python = "^0.2.0"
openai = "^1.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
pytest-mock = "^3.10.0"
```

#### 6.2 システム要件

- **ffmpeg**: システムにインストールされている必要があります
- **OpenAI API Key**: 環境変数またはコンストラクタで設定

#### 6.3 セットアップスクリプト

```bash
# ffmpegのインストール（macOS）
brew install ffmpeg

# ffmpegのインストール（Ubuntu）
sudo apt update
sudo apt install ffmpeg

# ffmpegのインストール（Windows）
# https://ffmpeg.org/download.html からダウンロード
```

### 7. 実装手順

#### Phase 3-2.1: 基本クラス実装
1. カスタム例外クラスの実装
2. `WhisperClient`クラスの基本構造実装
3. 初期化処理と一時ディレクトリ管理の実装

#### Phase 3-2.2: ファイル処理機能実装
1. 動画ファイル検証機能の実装
2. ffmpeg連携による音声抽出機能の実装
3. 一時ファイル管理とクリーンアップ機能の実装

#### Phase 3-2.3: API通信機能実装
1. Whisper API呼び出し機能の実装
2. リトライ機能とエラーハンドリングの実装
3. レスポンス検証機能の実装

#### Phase 3-2.4: データ変換機能実装
1. APIレスポンスからTranscriptionResultへの変換機能
2. セグメントデータの正規化処理
3. 時系列データの整合性チェック

#### Phase 3-2.5: テスト実装
1. 基本機能テストの実装
2. ファイル処理・音声抽出テストの実装
3. Integration Testの実装
4. テスト用ファイクスチャの準備

### 8. 完了条件

#### 必須条件
- [ ] `WhisperClient`クラスが正しく実装されている
- [ ] 動画ファイルから音声抽出が成功する
- [ ] 実際のWhisper APIとの通信が成功する
- [ ] タイムスタンプ付きセグメントが正しく生成される
- [ ] エラーハンドリングとリトライ機能が動作する
- [ ] 一時ファイルの適切なクリーンアップが行われる
- [ ] `mypy`による型チェックが通る
- [ ] 基本的なテストが全て通る
- [ ] Integration Testが通る（`INTEGRATION

_TEST=true`環境）
- [ ] docstringが適切に記載されている

#### 品質条件
- [ ] コードが`black`でフォーマットされている
- [ ] `flake8`のリンターチェックが通る
- [ ] テストカバレッジが90%以上
- [ ] 実際のAPI呼び出しでの動作確認完了
- [ ] 音声抽出品質の手動確認完了
- [ ] ffmpeg連携の安定性確認完了

### 9. 手動テスト項目

#### 9.1 音声抽出確認
1. **対応形式**: 様々な動画形式（mp4, avi, mov等）での音声抽出成功
2. **音質**: 抽出された音声の品質が文字起こしに適している
3. **ファイルサイズ**: 大きなファイルでの適切な処理
4. **エラー処理**: 破損ファイルや不正形式での適切なエラーハンドリング

#### 9.2 API連携確認
1. **正常系**: 実際の動画ファイルでWhisper APIを呼び出し、期待する形式のレスポンスが返ってくる
2. **エラー系**: 不正なAPIキー、ネットワークエラー、レート制限での適切なエラーハンドリング
3. **リトライ機能**: 一時的な障害からの自動復旧
4. **レスポンス品質**: 生成される文字起こしの精度が実用的

#### 9.3 データ変換確認
1. **セグメント生成**: タイムスタンプ付きセグメントの正確な生成
2. **時系列整合性**: セグメント間の時刻の論理的整合性
3. **テキスト品質**: 文字起こしテキストの品質と可読性
4. **オブジェクト変換**: `TranscriptionResult`への正確な変換

### 10. パフォーマンス考慮事項

#### 10.1 処理時間の最適化
- **音声抽出**: ffmpegの最適なパラメータ設定
- **API呼び出し**: 適切なタイムアウト設定
- **ファイル処理**: 大容量ファイルでのメモリ効率

#### 10.2 リソース管理
- **一時ファイル**: 適切なクリーンアップとディスク容量管理
- **メモリ使用量**: 大きな動画ファイル処理時のメモリ効率
- **並行処理**: 将来的な並行処理対応への考慮

### 11. セキュリティ考慮事項

#### 11.1 ファイル処理のセキュリティ
- **パストラバーサル**: ファイルパスの適切な検証
- **ファイルサイズ制限**: DoS攻撃防止のためのサイズ制限
- **一時ファイル**: 適切な権限設定とクリーンアップ

#### 11.2 API キー管理
- **環境変数**: APIキーの安全な管理方法
- **ログ出力**: APIキーがログに出力されないよう注意
- **エラーメッセージ**: APIキーが含まれないエラーメッセージ

### 12. 次フェーズへの引き継ぎ事項

#### Phase4（DraftGenerator実装）で必要となる情報
- `WhisperClient`の使用方法とインターフェース
- `TranscriptionResult`オブジェクトの構造と使用方法
- エラーハンドリングの統合方法
- 一時ファイル管理の考慮事項

#### Phase5（GenerateShortDraftUsecase実装）で必要となる情報
- 動画ファイル処理のフロー
- エラーハンドリングの統合パターン
- ファイル管理とクリーンアップの方法
- パフォーマンス最適化の考慮事項

### 13. トラブルシューティング

#### 13.1 よくある問題と解決方法

**ffmpegが見つからない**:
```bash
# 解決方法: ffmpegをインストール
brew install ffmpeg  # macOS
sudo apt install ffmpeg  # Ubuntu
```

**音声抽出に失敗する**:
- 動画ファイルの形式を確認
- ファイルの破損チェック
- ffmpegのバージョン確認

**API呼び出しが失敗する**:
- APIキーの有効性確認
- ネットワーク接続確認
- レート制限の確認

**メモリ不足エラー**:
- 動画ファイルのサイズ確認
- 一時ディスクの容量確認
- システムメモリの確認

#### 13.2 ログ出力とデバッグ

```python
import logging

# ログ設定例
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WhisperClientでのログ出力
logger.info(f"音声抽出開始: {video_path}")
logger.info(f"Whisper API呼び出し開始: {audio_path}")
logger.info(f"文字起こし完了: {len(result.segments)}セグメント生成")
```

### 14. 注意事項

#### 設計原則
- **堅牢性**: ファイル処理とAPI呼び出しでの適切なエラーハンドリング
- **効率性**: 大容量ファイルでの効率的な処理
- **保守性**: 明確な責任分離とテスタブルな設計
- **拡張性**: 将来的な機能追加に対応できる柔軟な設計

#### 実装時の注意点
- ffmpeg-pythonライブラリの最新仕様に準拠
- OpenAI Whisper APIの最新仕様に準拠
- 一時ファイルの適切な管理とクリーンアップ
- エラーメッセージは日本語で分かりやすく
- パフォーマンスとメモリ効率を考慮した実装

### 15. 将来の拡張可能性

#### 15.1 機能拡張
- **複数言語対応**: Whisper APIの言語指定機能
- **音声品質向上**: ノイズ除去やボリューム正規化
- **並行処理**: 複数ファイルの同時処理
- **キャッシュ機能**: 処理済みファイルのキャッシュ

#### 15.2 パフォーマンス改善
- **ストリーミング処理**: 大容量ファイルのストリーミング処理
- **GPU活用**: ローカルWhisperモデルでのGPU活用
- **圧縮**: 音声データの効率的な圧縮
- **分割処理**: 長時間動画の分割処理

この設計書に基づいて実装を進めることで、実用的で堅牢なWhisper API連携機能を構築できます。音声抽出からAPI呼び出し、データ変換まで一貫した処理フローを提供し、ショート動画制作に必要な高品質な文字起こし機能を実現します。
