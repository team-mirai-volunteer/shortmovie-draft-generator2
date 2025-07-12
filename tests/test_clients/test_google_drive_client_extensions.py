"""GoogleDriveClientの新機能テスト"""

from unittest.mock import Mock, patch

from src.clients.google_drive_client import GoogleDriveClient
from src.models.drive import DriveFile, DriveFolder


class TestGoogleDriveClientExtensions:
    """GoogleDriveClientの拡張機能テスト"""

    def setup_method(self):
        """テストセットアップ"""
        with patch("src.clients.google_drive_client.service_account"), patch("src.clients.google_drive_client.build"):
            self.client = GoogleDriveClient("dummy_path")
            self.client.service = Mock()

    def test_folder_exists_true(self):
        """フォルダが存在する場合のテスト"""
        self.client.service.files().list().execute.return_value = {"files": [{"id": "folder123", "name": "test_folder"}]}

        result = self.client.folder_exists("parent_id", "test_folder")

        assert result is True

    def test_folder_exists_false(self):
        """フォルダが存在しない場合のテスト"""
        self.client.service.files().list().execute.return_value = {"files": []}

        result = self.client.folder_exists("parent_id", "test_folder")

        assert result is False

    def test_list_folders(self):
        """サブフォルダ一覧取得のテスト"""
        with patch.object(self.client, "list_files") as mock_list_files:
            files = [
                DriveFile(name="folder1", file_id="id1", download_url="url1", mime_type="application/vnd.google-apps.folder"),
                DriveFile(name="video.mp4", file_id="id2", download_url="url2", mime_type="video/mp4"),
                DriveFile(name="folder2", file_id="id3", download_url="url3", mime_type="application/vnd.google-apps.folder"),
            ]
            mock_list_files.return_value = DriveFolder("parent_id", files)

            result = self.client.list_folders("folder_url")

            assert len(result) == 2
            assert all(f.mime_type == "application/vnd.google-apps.folder" for f in result)
