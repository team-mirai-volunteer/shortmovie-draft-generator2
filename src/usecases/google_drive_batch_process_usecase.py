"""Google Drive間バッチ処理ユースケース（リファクタリング版）"""

import tempfile
from pathlib import Path

from ..clients.google_drive_client import GoogleDriveClient, GoogleDriveError
from ..clients.slack_client import SlackClient
from ..models.drive import DriveFile
from ..models.result import GoogleDriveBatchResult
from .transcript_to_draft_usecase import TranscriptToDraftUsecase
from .video_to_transcript_usecase import VideoToTranscriptUsecase


class GoogleDriveBatchProcessUsecase:
    """Google Drive間バッチ処理ユースケース（リファクタリング版）

    責務:
    - Google Driveからの動画ダウンロード
    - VideoToTranscriptUsecaseとTranscriptToDraftUsecaseの順次実行
    - 結果ファイルのGoogle Driveアップロード
    - 全体のエラーハンドリングと結果統合
    """

    def __init__(
        self,
        video_to_transcript_usecase: VideoToTranscriptUsecase,
        transcript_to_draft_usecase: TranscriptToDraftUsecase,
        google_drive_client: GoogleDriveClient,
        slack_client: SlackClient | None = None,
    ):
        self.video_to_transcript_usecase = video_to_transcript_usecase
        self.transcript_to_draft_usecase = transcript_to_draft_usecase
        self.google_drive_client = google_drive_client
        self.slack_client = slack_client

    def execute_drive_batch(self, input_folder_url: str, output_folder_url: str) -> GoogleDriveBatchResult:
        """Google Drive間でのバッチ処理実行（リファクタリング版）

        Args:
            input_folder_url: 入力Google DriveフォルダURL
            output_folder_url: 出力Google DriveフォルダURL

        Returns:
            処理結果（GoogleDriveBatchResult）

        """
        try:
            # 1. 未処理動画の検出（既存ロジック維持）
            unprocessed_video = self._find_unprocessed_video_from_drive(input_folder_url, output_folder_url)

            if not unprocessed_video:
                return GoogleDriveBatchResult.no_unprocessed_videos()

            # 2. 動画処理開始通知
            self._send_processing_start_notification(unprocessed_video, input_folder_url)

            # 3. 出力フォルダの準備（既存ロジック維持）
            video_name = Path(unprocessed_video.name).stem
            output_folder_id = self.google_drive_client.extract_folder_id(output_folder_url)
            output_subfolder_id = self._prepare_output_subfolder(output_folder_id, video_name)

            with tempfile.TemporaryDirectory() as temp_dir:
                # 3. 動画ダウンロード
                video_path = self.google_drive_client.download_file(unprocessed_video, temp_dir)

                # 4. Phase 1: 動画→文字起こし
                transcript_result = self.video_to_transcript_usecase.execute(video_path, temp_dir)

                if not transcript_result.success:
                    error_msg = transcript_result.error_message or "文字起こし処理に失敗しました"
                    self._send_processing_failure_notification(unprocessed_video.name, error_msg)
                    return GoogleDriveBatchResult.from_error(error_msg)

                # 5. Phase 2: 文字起こし→企画書
                draft_result = self.transcript_to_draft_usecase.execute(transcript_result.transcript_file_path, temp_dir)

                if not draft_result.success:
                    error_msg = draft_result.error_message or "企画書生成処理に失敗しました"
                    self._send_processing_failure_notification(unprocessed_video.name, error_msg)
                    return GoogleDriveBatchResult.from_error(error_msg)

                # 6. 結果ファイルのアップロード
                draft_url = self.google_drive_client.upload_file(draft_result.draft_file_path, output_subfolder_id)
                subtitle_url = self.google_drive_client.upload_file(draft_result.subtitle_file_path, output_subfolder_id)
                video_url = self.google_drive_client.upload_file(video_path, output_subfolder_id)

                # 7. 中間ファイル（transcript.json）もアップロード（デバッグ用）
                transcript_url = self.google_drive_client.upload_file(transcript_result.transcript_file_path, output_subfolder_id)

                # 8. 出力サブフォルダのURLを生成
                output_subfolder_url = f"https://drive.google.com/drive/folders/{output_subfolder_id}"

                # 9. 処理完了通知
                self._send_processing_success_notification(unprocessed_video.name, output_subfolder_url)

                return GoogleDriveBatchResult(
                    success=True,
                    processed_video=unprocessed_video.name,
                    output_folder_id=output_subfolder_id,
                    draft_url=draft_url,
                    subtitle_url=subtitle_url,
                    video_url=video_url,
                    transcript_url=transcript_url,  # 新規追加
                    message=f"動画 '{unprocessed_video.name}' の処理が完了しました",
                )

        except Exception as e:
            error_msg = str(e)
            # 動画名が取得できている場合は失敗通知を送信
            if "unprocessed_video" in locals() and unprocessed_video:
                self._send_processing_failure_notification(unprocessed_video.name, error_msg)
            return GoogleDriveBatchResult.from_error(error_msg)

    def _prepare_output_subfolder(self, output_folder_id: str, video_name: str) -> str:
        """出力サブフォルダの準備（既存ロジックを分離）

        Args:
            output_folder_id: 出力フォルダID
            video_name: 動画名

        Returns:
            出力サブフォルダID

        """
        if not self.google_drive_client.folder_exists(output_folder_id, video_name):
            return self.google_drive_client.create_folder(video_name, output_folder_id)
        else:
            query = f"'{output_folder_id}' in parents and name='{video_name}' and mimeType='application/vnd.google-apps.folder'"
            results = self.google_drive_client.service.files().list(q=query, fields="files(id)", supportsAllDrives=True).execute()
            return str(results["files"][0]["id"])

    def _find_unprocessed_video_from_drive(self, input_folder_url: str, output_folder_url: str) -> DriveFile | None:
        """Google Driveフォルダから未処理動画を1本検出

        既存の_find_unprocessed_videoロジックをGoogle Drive対応に拡張

        処理ロジック:
        1. 入力フォルダから動画ファイル一覧を取得
        2. ファイル名順でソート（安定した処理順序）
        3. 出力フォルダ内に同名サブフォルダが存在しない動画を検索
        4. 最初に見つかった未処理動画を返す
        """
        try:
            input_folder = self.google_drive_client.list_files(input_folder_url)
            video_files = [f for f in input_folder.files if self._is_video_file(f)]

            if not video_files:
                return None

            video_files.sort(key=lambda x: x.name)

            output_folder_id = self.google_drive_client.extract_folder_id(output_folder_url)

            for video_file in video_files:
                video_name = Path(video_file.name).stem

                if not self.google_drive_client.folder_exists(output_folder_id, video_name):
                    return video_file

            return None

        except Exception as e:
            raise GoogleDriveError(f"未処理動画の検出に失敗しました: {e!s}") from e

    def _is_video_file(self, file: DriveFile) -> bool:
        """ファイルが動画ファイルかどうかを判定"""
        video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}
        video_mime_types = {"video/mp4", "video/avi", "video/quicktime", "video/x-msvideo", "video/x-ms-wmv", "video/x-flv", "video/webm"}

        return any(file.name.lower().endswith(ext) for ext in video_extensions) or file.mime_type in video_mime_types

    def _send_processing_start_notification(self, video_file: DriveFile, input_folder_url: str) -> None:
        """動画処理開始通知を送信"""
        if not self.slack_client:
            return

        try:
            message = f"🎬 動画処理を開始しました\n📁 ファイル名: {video_file.name}\n🔗 入力フォルダ: {input_folder_url}"
            self.slack_client.send_message(message)
        except Exception as e:
            # 通知の失敗は処理を止めない
            print(f"Slack通知の送信に失敗しました: {e}")

    def _send_processing_success_notification(self, video_name: str, output_subfolder_url: str) -> None:
        """動画処理完了通知を送信"""
        if not self.slack_client:
            return

        try:
            message = f"✅ 台本生成が完了しました\n📁 動画ファイル名: {video_name}\n🔗 出力フォルダ: {output_subfolder_url}"
            self.slack_client.send_message(message)
        except Exception as e:
            # 通知の失敗は処理を止めない
            print(f"Slack通知の送信に失敗しました: {e}")

    def _send_processing_failure_notification(self, video_name: str, error_message: str) -> None:
        """動画処理失敗通知を送信"""
        if not self.slack_client:
            return

        try:
            message = f"❌ 台本生成に失敗しました\n📁 動画ファイル名: {video_name}\n💥 エラー理由: {error_message}"
            self.slack_client.send_message(message)
        except Exception as e:
            # 通知の失敗は処理を止めない
            print(f"Slack通知の送信に失敗しました: {e}")
