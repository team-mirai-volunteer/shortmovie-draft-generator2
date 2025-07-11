"""Google Drive間バッチ処理ユースケース"""

import tempfile
from pathlib import Path
from typing import Optional

from ..clients.google_drive_client import GoogleDriveClient, GoogleDriveError
from ..models.drive import DriveFile
from ..models.result import GoogleDriveBatchResult
from .generate_short_draft_usecase import GenerateShortDraftUsecase


class GoogleDriveBatchProcessUsecase:
    """Google Drive入力・出力対応バッチ処理ユースケース

    Google Driveフォルダ間でのバッチ処理を実行し、
    既存の_find_unprocessed_videoロジックをGoogle Drive対応に拡張する。
    """

    def __init__(self, generate_usecase: GenerateShortDraftUsecase, google_drive_client: GoogleDriveClient):
        self.generate_usecase = generate_usecase
        self.google_drive_client = google_drive_client

    def execute_drive_batch(self, input_folder_url: str, output_folder_url: str) -> GoogleDriveBatchResult:
        """Google Drive間でのバッチ処理実行

        Args:
            input_folder_url: 入力Google DriveフォルダURL
            output_folder_url: 出力Google DriveフォルダURL

        Returns:
            処理結果（GoogleDriveBatchResult）
        """
        try:
            unprocessed_video = self._find_unprocessed_video_from_drive(input_folder_url, output_folder_url)

            if not unprocessed_video:
                return GoogleDriveBatchResult.no_unprocessed_videos()

            video_name = Path(unprocessed_video.name).stem
            output_folder_id = self.google_drive_client.extract_folder_id(output_folder_url)

            if not self.google_drive_client.folder_exists(output_folder_id, video_name):
                output_subfolder_id = self.google_drive_client.create_folder(video_name, output_folder_id)
            else:
                query = f"'{output_folder_id}' in parents and name='{video_name}' and mimeType='application/vnd.google-apps.folder'"
                results = self.google_drive_client.service.files().list(q=query, fields="files(id)", supportsAllDrives=True).execute()
                output_subfolder_id = results["files"][0]["id"]

            with tempfile.TemporaryDirectory() as temp_dir:
                video_path = self.google_drive_client.download_file(unprocessed_video, temp_dir)

                result = self.generate_usecase.execute(video_path, temp_dir)

                if not result.success:
                    return GoogleDriveBatchResult.from_error(result.error_message or "処理に失敗しました")

                draft_url = self.google_drive_client.upload_file(result.draft_file_path, output_subfolder_id)
                subtitle_url = self.google_drive_client.upload_file(result.subtitle_file_path, output_subfolder_id)
                video_url = self.google_drive_client.upload_file(video_path, output_subfolder_id)

                return GoogleDriveBatchResult(
                    success=True,
                    processed_video=unprocessed_video.name,
                    output_folder_id=output_subfolder_id,
                    draft_url=draft_url,
                    subtitle_url=subtitle_url,
                    video_url=video_url,
                    message=f"動画 '{unprocessed_video.name}' の処理が完了しました",
                )

        except Exception as e:
            return GoogleDriveBatchResult.from_error(str(e))

    def _find_unprocessed_video_from_drive(self, input_folder_url: str, output_folder_url: str) -> Optional[DriveFile]:
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
            raise GoogleDriveError(f"未処理動画の検出に失敗しました: {str(e)}")

    def _is_video_file(self, file: DriveFile) -> bool:
        """ファイルが動画ファイルかどうかを判定"""
        video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}
        video_mime_types = {"video/mp4", "video/avi", "video/quicktime", "video/x-msvideo", "video/x-ms-wmv", "video/x-flv", "video/webm"}

        return any(file.name.lower().endswith(ext) for ext in video_extensions) or file.mime_type in video_mime_types
