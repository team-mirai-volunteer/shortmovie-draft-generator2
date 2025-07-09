# ショート動画設計図生成プロジェクト

単一の動画ファイルを入力として、ショート動画作成用の設計図（企画書）を自動生成するPythonプロジェクト。

## 機能

- 動画ファイルからWhisper APIを使用した音声文字起こし
- ChatGPT APIを使用したショート動画企画書の生成
- 切り抜き箇所（開始・終了時刻）、タイトル案、キャプション案を含むマークダウン形式の企画書出力
- SRT形式の字幕ファイル出力

## 技術要件

- Python 3.8.1+
- Poetry（パッケージ管理）
- mypy（型チェック）
- 依存性注入（DI）パターンの採用
- ローカルCLIとして動作

## インストール

```bash
poetry install
```

## 使用方法

```bash
poetry run python src/main.py input/video.mp4 output/
```

## 開発

### テスト実行

```bash
poetry run pytest
```

### 型チェック

```bash
poetry run mypy src/
```

### コードフォーマット

```bash
poetry run black src/ tests/
```

### リンター

```bash
poetry run flake8 src/ tests/
