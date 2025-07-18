# ショート動画設計図生成プロジェクト

単一の動画ファイルを入力として、ショート動画作成用の設計図（企画書）を自動生成する Python プロジェクト。

## 機能

- 動画ファイルから Whisper API を使用した音声文字起こし
- ChatGPT API を使用したショート動画企画書の生成
- 切り抜き箇所（開始・終了時刻）、タイトル案、キャプション案を含むマークダウン形式の企画書出力
- SRT 形式の字幕ファイル出力
- **Google Drive 連携による自動処理**

## 技術要件

- Python 3.8.1+
- uv（パッケージ管理）
- mypy（型チェック）
- 依存性注入（DI）パターンの採用
- Google Drive API v3（サービスアカウント認証）

## インストール

```bash
uv sync
```

## 環境設定

### 1. 環境変数ファイルの作成

`.env.example`をコピーして`.env`ファイルを作成してください：

```bash
cp .env.example .env
```

### 2. 必須環境変数の設定

#### OpenAI API 設定

```bash
# 必須: OpenAI APIキーを設定してください
OPENAI_API_KEY=your_actual_openai_api_key_here

# オプション: モデル設定（デフォルト値）
CHATGPT_MODEL=gpt-4o
WHISPER_MODEL=whisper-1
```

#### Google Drive API 設定（メイン機能）

```bash
# 必須: サービスアカウント認証 (いずれか1つを選択)
# オプション1: ファイルパス
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=path/to/service-account-key.json
# オプション2: JSON文字列
GOOGLE_SERVICE_ACCOUNT_KEY_JSON='{"type":"service_account","project_id":"..."}'
# オプション3: Base64エンコードされたJSON (Cloud Run Job推奨)
GOOGLE_SERVICE_ACCOUNT_KEY_BASE64=eyJ0eXBlIjoic2VydmljZV9hY2NvdW50IiwicHJvamVjdF9pZCI6Li4ufQ==

# 必須: 入力・出力フォルダURL
INPUT_DRIVE_FOLDER=https://drive.google.com/drive/folders/input_folder_id
OUTPUT_DRIVE_FOLDER=https://drive.google.com/drive/folders/output_folder_id
```

### 3. Google Drive API 設定手順

#### 3.1 Google Cloud Project の設定

1. **Google Cloud Console にアクセス**

   - [Google Cloud Console](https://console.cloud.google.com/)にログイン

2. **新しいプロジェクトを作成**

   - プロジェクト名: `shortmovie-draft-generator`

3. **Google Drive API の有効化**
   - API とサービス → ライブラリ
   - "Google Drive API"を検索して有効化

#### 3.2 サービスアカウントの作成

1. **サービスアカウントの作成**

   - IAM と管理 → サービスアカウント
   - 「サービスアカウントを作成」をクリック
   - 名前: `shortmovie-drive-access`
   - 説明: `ショート動画企画書生成用のGoogle Driveアクセス`

2. **サービスアカウントキーの作成**
   - 作成したサービスアカウントをクリック
   - 「キー」タブ → 「キーを追加」→ 「新しいキーを作成」
   - 形式: JSON
   - ダウンロードした JSON ファイルを安全な場所に保存

#### 3.3 Google Drive フォルダの共有設定

1. **入力・出力フォルダを Google Drive で作成**
2. **各フォルダを右クリック → 「共有」を選択**
3. **サービスアカウントのメールアドレスを追加**
   - JSON ファイル内の`client_email`の値をコピー
   - 権限: 「編集者」（出力フォルダ）、「閲覧者」（入力フォルダでも可）
4. **フォルダ URL をコピーして環境変数に設定**

### 4. システム要件

このプロジェクトは動画処理に ffmpeg を使用します。事前にインストールしてください：

**macOS:**

```bash
brew install ffmpeg
```

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
[FFmpeg 公式サイト](https://ffmpeg.org/download.html)からダウンロードしてインストールしてください。

## 使用方法

### Google Drive 連携での処理（メイン）

#### 単発処理

環境変数で設定したフォルダから 1 つの動画を処理：

```bash
uv run python src/main.py --drive-batch
```

#### 処理の流れ

1. `INPUT_DRIVE_FOLDER`から未処理の動画を 1 つ検出
2. 動画をダウンロードして処理（音声文字起こし → 企画書生成）
3. 企画書・字幕・元動画を`OUTPUT_DRIVE_FOLDER`にアップロード
4. 連続処理の場合、すべての動画が処理されるまで繰り返し

#### 出力構造

```
OUTPUT_DRIVE_FOLDER/
├── video1/
│   ├── draft.md          # 企画書
│   ├── subtitle.srt      # 字幕ファイル
│   └── video1.mp4        # 元動画
├── video2/
│   ├── draft.md
│   ├── subtitle.srt
│   └── video2.mp4
└── ...
```

## 開発・動作確認用（ローカルファイル処理）

### ローカルファイルでの処理

```bash
uv run python src/main.py input/video.mp4 output/
```

### Google Drive フォルダから単発処理

```bash
uv run python src/main.py "https://drive.google.com/drive/folders/abc123" output/ --drive
```

### Google Drive アップロード付きローカル処理

```bash
uv run python src/main.py input/video.mp4 output/ --upload --upload-folder-id "folder_id"
```

## デバッグ・開発用ツール

### TranscriptToDraftUsecase デバッグスクリプト

既存の文字起こしファイル（transcript.json）から企画書と字幕ファイルを生成するデバッグ用スクリプトです。
文字起こし処理をスキップして、企画書生成部分のみをテストできます。

#### 基本的な使用方法

```bash
# サンプルファイルを使用してテスト
python debug_transcript_to_draft.py intermediate/sample_transcript.json output/

# 詳細ログ付きで実行
python debug_transcript_to_draft.py intermediate/sample_transcript.json output/ --verbose

# 既存のtranscript.jsonファイルを使用
python debug_transcript_to_draft.py intermediate/your_video_transcript.json output/
```

#### 使用例

```bash
# サンプルファイルでテスト実行
$ python debug_transcript_to_draft.py intermediate/sample_transcript.json output/ -v
=== TranscriptToDraftUsecase デバッグスクリプト ===
入力ファイル: intermediate/sample_transcript.json
出力ディレクトリ: output

🔧 TranscriptToDraftUsecaseを初期化中...
✓ 初期化完了
📝 企画書生成を開始します...
🎉 企画書生成が正常に完了しました！

生成されたファイル:
  📄 企画書: output/sample_video_draft.md
  📝 字幕: output/sample_video_subtitle.srt
```

#### メリット

- **高速テスト**: 文字起こし処理（時間がかかる）をスキップ
- **企画書生成のデバッグ**: ChatGPT APIの応答やプロンプトの調整をテスト
- **文字起こし結果の修正**: transcript.jsonを手動編集して再実行可能
- **開発効率向上**: 企画書生成ロジックの改善時に便利

## 開発

### テスト実行

```bash
uv run pytest
```

### 型チェック

```bash
uv run mypy src/
```

### コードフォーマット・リンター

```bash
# フォーマットチェック
uv run ruff check src/ tests/

# 自動修正
uv run ruff check --fix src/ tests/

# コードフォーマット
uv run ruff format src/ tests/
```
