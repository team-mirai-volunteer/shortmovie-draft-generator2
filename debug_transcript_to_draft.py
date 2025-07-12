#!/usr/bin/env python3
"""TranscriptToDraftUsecase デバッグ用スクリプト

既存のtranscript.jsonファイルから企画書と字幕ファイルを生成するデバッグ用スクリプト。
文字起こし処理をスキップして、企画書生成部分のみをテストできます。

使用例:
    python debug_transcript_to_draft.py intermediate/video_transcript.json output/
    python debug_transcript_to_draft.py intermediate/video_transcript.json output/ --verbose
"""

import os
import sys
import traceback
from pathlib import Path

import click
from dotenv import load_dotenv

from src.builders.prompt_builder import PromptBuilder
from src.clients.chatgpt_client import ChatGPTClient
from src.service.srt_generator import SrtGenerator
from src.usecases.transcript_to_draft_usecase import TranscriptToDraftUsecase


def setup_usecase() -> TranscriptToDraftUsecase:
    """TranscriptToDraftUsecaseのセットアップ"""
    # 環境変数を読み込み
    load_dotenv()

    # 必須環境変数の確認
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        click.echo("❌ エラー: OPENAI_API_KEY 環境変数が設定されていません", err=True)
        click.echo("以下の環境変数を設定してください:", err=True)
        click.echo("  OPENAI_API_KEY=your_openai_api_key", err=True)
        sys.exit(1)

    # ChatGPTモデルの設定
    chatgpt_model = os.getenv("CHATGPT_MODEL", "gpt-4o")

    # 各コンポーネントの初期化
    chatgpt_client = ChatGPTClient(api_key=openai_api_key, model=chatgpt_model)
    prompt_builder = PromptBuilder()
    srt_generator = SrtGenerator()

    # TranscriptToDraftUsecaseの初期化
    return TranscriptToDraftUsecase(chatgpt_client=chatgpt_client, prompt_builder=prompt_builder, srt_generator=srt_generator)


@click.command()
@click.argument("transcript_file", type=click.Path(exists=True, path_type=Path))
@click.argument("output_dir", type=click.Path(path_type=Path))
@click.option("--verbose", "-v", is_flag=True, help="詳細なログを出力します")
def main(transcript_file: Path, output_dir: Path, verbose: bool) -> None:
    """transcript.jsonから企画書と字幕ファイルを生成

    Args:
        transcript_file: 文字起こしJSONファイルのパス
        output_dir: 出力ディレクトリのパス
        verbose: 詳細ログの有効化

    """
    try:
        if verbose:
            click.echo("=== TranscriptToDraftUsecase デバッグスクリプト ===")
            click.echo(f"入力ファイル: {transcript_file}")
            click.echo(f"出力ディレクトリ: {output_dir}")
            click.echo("")

        # Usecaseのセットアップ
        if verbose:
            click.echo("🔧 TranscriptToDraftUsecaseを初期化中...")

        usecase = setup_usecase()

        if verbose:
            click.echo("✓ 初期化完了")
            click.echo("📝 企画書生成を開始します...")

        # 企画書生成の実行
        result = usecase.execute(str(transcript_file), str(output_dir))

        if result.success:
            click.echo("🎉 企画書生成が正常に完了しました！")
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
            click.echo("❌ 企画書生成中にエラーが発生しました", err=True)
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
