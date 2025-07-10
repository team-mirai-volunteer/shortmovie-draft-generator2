"""ショート動画設計図生成プロジェクト メインエントリーポイント"""

import os
import sys
from pathlib import Path
import click
from dotenv import load_dotenv

from src.clients.whisper_client import WhisperClient
from src.clients.chatgpt_client import ChatGPTClient
from src.clients.google_drive_client import GoogleDriveClient
from src.builders.prompt_builder import PromptBuilder
from src.service.draft_generator import DraftGenerator
from src.service.srt_generator import SrtGenerator
from src.usecases.generate_short_draft_usecase import GenerateShortDraftUsecase


class DIContainer:
    """依存性注入コンテナ

    アプリケーションで使用するサービスの初期化と依存関係の管理を行います。
    """

    def __init__(self) -> None:
        """環境変数を読み込み、各サービスを初期化"""
        load_dotenv()

        self.openai_api_key = self._get_required_env("OPENAI_API_KEY")
        self.chatgpt_model = os.getenv("CHATGPT_MODEL", "gpt-4o")
        self.whisper_model = os.getenv("WHISPER_MODEL", "whisper-1")

        self.whisper_client = WhisperClient(api_key=self.openai_api_key, model=self.whisper_model)

        self.chatgpt_client = ChatGPTClient(api_key=self.openai_api_key, model=self.chatgpt_model)

        self.google_drive_client = GoogleDriveClient()

        self.prompt_builder = PromptBuilder()

        self.draft_generator = DraftGenerator(
            whisper_client=self.whisper_client,
            chatgpt_client=self.chatgpt_client,
            prompt_builder=self.prompt_builder,
        )

        self.srt_generator = SrtGenerator()

        self.generate_usecase = GenerateShortDraftUsecase(
            draft_generator=self.draft_generator, srt_generator=self.srt_generator, google_drive_client=self.google_drive_client
        )

    def _get_required_env(self, key: str) -> str:
        """必須環境変数を取得

        Args:
            key: 環境変数名

        Returns:
            環境変数の値

        Raises:
            SystemExit: 環境変数が設定されていない場合
        """
        value = os.getenv(key)
        if not value:
            click.echo(f"エラー: 環境変数 {key} が設定されていません", err=True)
            click.echo("以下の環境変数を設定してください:", err=True)
            click.echo("  OPENAI_API_KEY=your_openai_api_key", err=True)
            click.echo("", err=True)
            click.echo("オプション:", err=True)
            click.echo("  CHATGPT_MODEL=gpt-4  # デフォルト: gpt-4", err=True)
            click.echo("  WHISPER_MODEL=whisper-1  # デフォルト: whisper-1", err=True)
            sys.exit(1)
        return value


@click.command()
@click.argument("input_source", type=str)
@click.argument("output_dir", type=click.Path(path_type=Path))
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="詳細なログを出力します",
)
@click.option("--drive", is_flag=True, help="Google DriveフォルダURLとして処理")
def main(input_source: str, output_dir: Path, verbose: bool, drive: bool) -> None:
    """動画ファイルまたはGoogle Driveフォルダからショート動画企画書を生成

    INPUT_SOURCE: 動画ファイルのパスまたはGoogle DriveフォルダURL
    OUTPUT_DIR: 企画書と字幕ファイルの出力ディレクトリ

    例:
        poetry run python src/main.py input/video.mp4 output/

        poetry run python src/main.py "https://drive.google.com/drive/folders/abc123?usp=sharing" output/ --drive
    """
    try:
        if verbose:
            mode_text = "Google Drive連携" if drive else "ローカルファイル"
            click.echo(f"=== ショート動画設計図生成プロジェクト（{mode_text}） ===")
            click.echo(f"入力ソース: {input_source}")
            click.echo(f"出力ディレクトリ: {output_dir}")
            click.echo("")

        container = DIContainer()

        if verbose:
            click.echo("✓ 依存関係の初期化が完了しました")
            if drive:
                click.echo("🔍 Google Driveフォルダから動画ファイルを検索中...")
            else:
                click.echo("📹 動画の処理を開始します...")

        if drive:
            result = container.generate_usecase.execute_from_drive(input_source, str(output_dir))
        else:
            if not Path(input_source).exists():
                click.echo(f"❌ 動画ファイルが存在しません: {input_source}", err=True)
                sys.exit(1)
            result = container.generate_usecase.execute(input_source, str(output_dir))

        if result.success:
            click.echo("🎉 処理が正常に完了しました！")
            click.echo("")
            click.echo("生成されたファイル:")
            click.echo(f"  📄 企画書: {result.draft_file_path}")
            click.echo(f"  📝 字幕: {result.subtitle_file_path}")

            if verbose:
                click.echo("")
                click.echo("次のステップ:")
                click.echo("1. 企画書を確認して、気に入った企画を選択してください")
                click.echo("2. 字幕ファイルを動画編集ソフトで読み込んでください")
                click.echo("3. 企画書の時間指定に従って動画をカットしてください")

        else:
            click.echo("❌ 処理中にエラーが発生しました", err=True)
            click.echo(f"エラー内容: {result.error_message}", err=True)
            sys.exit(1)

    except KeyboardInterrupt:
        click.echo("\n⚠️  処理が中断されました", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ 予期しないエラーが発生しました: {str(e)}", err=True)
        if verbose:
            import traceback

            click.echo("\nスタックトレース:", err=True)
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
