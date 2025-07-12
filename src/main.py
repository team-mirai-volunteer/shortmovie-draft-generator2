"""ショート動画設計図生成プロジェクト メインエントリーポイント"""

import os
import sys
import traceback
from pathlib import Path

import click
from dotenv import load_dotenv

from src.builders.prompt_builder import PromptBuilder
from src.clients.chatgpt_client import ChatGPTClient
from src.clients.google_drive_client import GoogleDriveClient
from src.clients.slack_client import SlackClient
from src.clients.whisper_client import WhisperClient
from src.models.result import GenerateResult
from src.service.draft_generator import DraftGenerator
from src.service.srt_generator import SrtGenerator
from src.usecases.google_drive_batch_process_usecase import GoogleDriveBatchProcessUsecase
from src.usecases.transcript_to_draft_usecase import TranscriptToDraftUsecase
from src.usecases.video_to_transcript_usecase import VideoToTranscriptUsecase


class DIContainer:
    """依存性注入コンテナ

    アプリケーションで使用するサービスの初期化と依存関係の管理を行います。
    """

    def __init__(self) -> None:
        """各サービスを初期化（環境変数は事前に読み込み済み）"""
        # 既存の設定
        self.openai_api_key = self._get_required_env("OPENAI_API_KEY")
        self.chatgpt_model = os.getenv("CHATGPT_MODEL", "gpt-4o")
        self.whisper_model = os.getenv("WHISPER_MODEL", "whisper-1")

        # Google Drive API設定（サービスアカウント）
        # Cloud Runではオプショナル、ローカルでは必須
        self.google_service_account_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY_PATH")
        self.google_service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY_JSON")  # JSON文字列として直接指定
        self.google_service_account_base64 = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY_BASE64")  # base64エンコードされたJSON
        self.google_drive_upload_folder_id = os.getenv("GOOGLE_DRIVE_UPLOAD_FOLDER_ID")

        # Google Driveバッチ処理用（新規追加）
        self.input_drive_folder = os.getenv("INPUT_DRIVE_FOLDER") or os.getenv("GOOGLE_DRIVE_SOURCE_FOLDER_URL")
        self.output_drive_folder = os.getenv("OUTPUT_DRIVE_FOLDER") or os.getenv("GOOGLE_DRIVE_DESTINATION_FOLDER_URL")

        # Slack通知設定（オプショナル）
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self.slack_notifications_enabled = os.getenv("SLACK_NOTIFICATIONS_ENABLED", "false").lower() == "true"

        self.whisper_client = WhisperClient(api_key=self.openai_api_key, model=self.whisper_model)

        self.chatgpt_client = ChatGPTClient(api_key=self.openai_api_key, model=self.chatgpt_model)

        # Cloud Runでの実行時はADCを使用、ローカルではキーファイルまたはJSON文字列を使用
        self.google_drive_client = GoogleDriveClient(
            service_account_path=self.google_service_account_path if self.google_service_account_path else None,
            service_account_json=self.google_service_account_json if self.google_service_account_json else None,
            service_account_base64=self.google_service_account_base64 if self.google_service_account_base64 else None,
        )

        self.prompt_builder = PromptBuilder()

        self.draft_generator = DraftGenerator(
            whisper_client=self.whisper_client,
            chatgpt_client=self.chatgpt_client,
            prompt_builder=self.prompt_builder,
        )

        self.srt_generator = SrtGenerator()

        # SlackClientの初期化（WebHook URLが設定されている場合のみ）
        self.slack_client = None
        if self.slack_webhook_url and self.slack_notifications_enabled:
            self.slack_client = SlackClient(self.slack_webhook_url)

        # 新しいUsecaseの初期化
        self.video_to_transcript_usecase = VideoToTranscriptUsecase(whisper_client=self.whisper_client)

        self.transcript_to_draft_usecase = TranscriptToDraftUsecase(
            chatgpt_client=self.chatgpt_client, prompt_builder=self.prompt_builder, srt_generator=self.srt_generator
        )

        # リファクタリング後のGoogleDriveBatchProcessUsecase（Slack通知対応）
        self.google_drive_batch_usecase = GoogleDriveBatchProcessUsecase(
            video_to_transcript_usecase=self.video_to_transcript_usecase,
            transcript_to_draft_usecase=self.transcript_to_draft_usecase,
            google_drive_client=self.google_drive_client,
            slack_client=self.slack_client,  # 新規追加
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
            click.echo("  GOOGLE_SERVICE_ACCOUNT_KEY_PATH=path/to/service-account-key.json", err=True)
            click.echo("  # または", err=True)
            click.echo('  GOOGLE_SERVICE_ACCOUNT_KEY_JSON=\'{"type":"service_account","project_id":"..."}\'  # JSON文字列として直接指定', err=True)
            click.echo("  # または", err=True)
            click.echo("  GOOGLE_SERVICE_ACCOUNT_KEY_BASE64='eyJ0eXBlIjoic2VydmljZV9hY2NvdW50IiwicHJv...'  # base64エンコードされたJSON", err=True)
            click.echo("", err=True)
            click.echo("オプション:", err=True)
            click.echo("  CHATGPT_MODEL=gpt-4o  # デフォルト: gpt-4o", err=True)
            click.echo("  WHISPER_MODEL=whisper-1  # デフォルト: whisper-1", err=True)
            sys.exit(1)
        return value


@click.command()
@click.argument("input_source", type=str, required=False)
@click.argument("output_dir", type=click.Path(path_type=Path), required=False)
@click.option("--batch", is_flag=True, help="バッチ処理モード（ローカル）")
@click.option("--drive-batch", is_flag=True, help="Google Driveバッチ処理モード")
@click.option("--input-drive-folder", type=str, help="入力Google DriveフォルダURL")
@click.option("--output-drive-folder", type=str, help="出力Google DriveフォルダURL")
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="詳細なログを出力します",
)
@click.option("--drive", is_flag=True, help="Google DriveフォルダURLとして処理")
@click.option("--upload", is_flag=True, help="生成されたファイルをGoogle Driveにアップロードする")
@click.option("--upload-folder-id", help="アップロード先のGoogle DriveフォルダID")
def main(
    input_source: str,
    output_dir: Path,
    batch: bool,
    drive_batch: bool,
    input_drive_folder: str,
    output_drive_folder: str,
    verbose: bool,
    drive: bool,
    upload: bool,
    upload_folder_id: str,
) -> None:
    """動画ファイルまたはGoogle Driveフォルダからショート動画企画書を生成

    INPUT_SOURCE: 動画ファイルのパスまたはGoogle DriveフォルダURL（--drive-batchモード以外で必須）
    OUTPUT_DIR: 企画書と字幕ファイルの出力ディレクトリ（--drive-batchモード以外で必須）

    例:
        poetry run python src/main.py input/video.mp4 output/

        poetry run python src/main.py "https://drive.google.com/drive/folders/abc123?usp=sharing" output/ --drive

        poetry run python src/main.py --drive-batch --input-drive-folder "https://drive.google.com/..." --output-drive-folder "https://drive.google.com/..."
    """
    try:
        # 環境変数を最初に読み込み
        load_dotenv()
        if drive_batch:
            input_folder = input_drive_folder or os.getenv("INPUT_DRIVE_FOLDER") or os.getenv("GOOGLE_DRIVE_SOURCE_FOLDER_URL")
            output_folder = output_drive_folder or os.getenv("OUTPUT_DRIVE_FOLDER") or os.getenv("GOOGLE_DRIVE_DESTINATION_FOLDER_URL")

            if not input_folder or not output_folder:
                click.echo("❌ Google Driveバッチ処理には --input-drive-folder と --output-drive-folder オプション、または環境変数の設定が必要です", err=True)
                sys.exit(1)

            # Type narrowing: input_folder and output_folder are guaranteed to be str at this point
            input_folder_str: str = input_folder
            output_folder_str: str = output_folder
        elif not input_source or not output_dir:
            click.echo("❌ 通常モードでは INPUT_SOURCE と OUTPUT_DIR が必要です", err=True)
            sys.exit(1)

        if verbose:
            if drive_batch:
                mode_text = "Google Driveバッチ処理"
            elif drive:
                mode_text = "Google Drive連携"
            else:
                mode_text = "ローカルファイル"
            click.echo(f"=== ショート動画設計図生成プロジェクト（{mode_text}） ===")
            if not drive_batch:
                click.echo(f"入力ソース: {input_source}")
                click.echo(f"出力ディレクトリ: {output_dir}")
            else:
                click.echo(f"入力フォルダ: {input_folder_str}")
                click.echo(f"出力フォルダ: {output_folder_str}")
            click.echo("")

        container = DIContainer()

        if upload:
            click.echo("❌ --uploadオプションは現在サポートされていません。--drive-batchを使用してください。", err=True)
            sys.exit(1)

        if verbose:
            click.echo("✓ 依存関係の初期化が完了しました")
            if drive_batch:
                click.echo("🔄 Google Driveバッチ処理を開始します...")
            elif drive:
                click.echo("🔍 Google Driveフォルダから動画ファイルを検索中...")
            else:
                click.echo("📹 動画の処理を開始します...")

        if drive_batch:
            # input_folder and output_folder are guaranteed to be str at this point
            batch_result = container.google_drive_batch_usecase.execute_drive_batch(input_folder_str, output_folder_str)

            if batch_result.success:
                if batch_result.processed_video:
                    click.echo("🎉 バッチ処理が正常に完了しました！")
                    click.echo(f"🎬 処理済み動画: {batch_result.processed_video}")
                    click.echo(f"📄 企画書: {batch_result.draft_url}")
                    click.echo(f"📝 字幕: {batch_result.subtitle_url}")
                    click.echo(f"🎥 動画: {batch_result.video_url}")
                    if batch_result.transcript_url:
                        click.echo(f"📋 文字起こし: {batch_result.transcript_url}")
                else:
                    click.echo("ℹ️ 処理対象の動画がありませんでした")
            else:
                click.echo("❌ バッチ処理中にエラーが発生しました", err=True)
                click.echo(f"エラー内容: {batch_result.error_message}", err=True)
                sys.exit(1)
            return

        if drive:
            # Google Drive処理は複雑なので、一旦エラーとして処理
            click.echo("❌ --driveオプションは現在サポートされていません。--drive-batchを使用してください。", err=True)
            sys.exit(1)
        else:
            if not Path(input_source).exists():
                click.echo(f"❌ 動画ファイルが存在しません: {input_source}", err=True)
                sys.exit(1)

            # 新しい2段階処理を使用
            if verbose:
                click.echo("📋 文字起こしを開始します...")

            transcript_result = container.video_to_transcript_usecase.execute(input_source, "intermediate")
            if not transcript_result.success:
                click.echo(f"❌ 文字起こし処理中にエラーが発生しました: {transcript_result.error_message}", err=True)
                sys.exit(1)

            if verbose:
                click.echo(f"✓ 文字起こし完了: {transcript_result.transcript_file_path}")
                click.echo("📝 企画書生成を開始します...")

            draft_result = container.transcript_to_draft_usecase.execute(transcript_result.transcript_file_path, str(output_dir))
            if not draft_result.success:
                click.echo(f"❌ 企画書生成処理中にエラーが発生しました: {draft_result.error_message}", err=True)
                sys.exit(1)

            # GenerateResultと同じ形式で結果を作成
            result = GenerateResult(draft_file_path=draft_result.draft_file_path, subtitle_file_path=draft_result.subtitle_file_path, success=True)

        if result.success:
            click.echo("🎉 処理が正常に完了しました！")
            click.echo("")
            click.echo("生成されたファイル:")
            click.echo(f"  📄 企画書: {result.draft_file_path}")
            click.echo(f"  📝 字幕: {result.subtitle_file_path}")

            if result.uploaded_draft_url:
                click.echo(f"  ☁️ 企画書 (Google Drive): {result.uploaded_draft_url}")
            if result.uploaded_subtitle_url:
                click.echo(f"  ☁️ 字幕 (Google Drive): {result.uploaded_subtitle_url}")

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
        click.echo(f"❌ 予期しないエラーが発生しました: {e!s}", err=True)
        if verbose:
            click.echo("\nスタックトレース:", err=True)
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
