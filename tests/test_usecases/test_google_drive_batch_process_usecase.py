"""GoogleDriveBatchProcessUsecaseのテスト"""

from unittest.mock import Mock, patch

from src.models.drive import DriveFile, DriveFolder
from src.models.result import GenerateResult
from src.usecases.google_drive_batch_process_usecase import GoogleDriveBatchProcessUsecase


class TestGoogleDriveBatchProcessUsecase:
    """GoogleDriveBatchProcessUsecaseのテストクラス"""

    def setup_method(self):
        """テストセットアップ"""
        self.mock_generate_usecase = Mock()
        self.mock_google_drive_client = Mock()
        self.usecase = GoogleDriveBatchProcessUsecase(self.mock_generate_usecase, self.mock_google_drive_client)

    def test_execute_drive_batch_success(self):
        """正常なバッチ処理のテスト"""
        video_file = DriveFile(name="test_video.mp4", file_id="file123", download_url="url", mime_type="video/mp4", size=1024)
        self.usecase._find_unprocessed_video_from_drive = Mock(return_value=video_file)  # type: ignore[method-assign]
        self.mock_google_drive_client.extract_folder_id.return_value = "output_folder_id"
        self.mock_google_drive_client.folder_exists.return_value = False
        self.mock_google_drive_client.create_folder.return_value = "subfolder_id"
        self.mock_google_drive_client.download_file.return_value = "/tmp/test_video.mp4"

        generate_result = GenerateResult(draft_file_path="/tmp/draft.md", subtitle_file_path="/tmp/subtitle.srt", success=True)
        self.mock_generate_usecase.execute.return_value = generate_result

        self.mock_google_drive_client.upload_file.side_effect = ["draft_url", "subtitle_url", "video_url"]

        with patch("tempfile.TemporaryDirectory") as mock_temp:
            mock_temp.return_value.__enter__.return_value = "/tmp"
            result = self.usecase.execute_drive_batch("input_folder_url", "output_folder_url")

        assert result.success is True
        assert result.processed_video == "test_video.mp4"
        assert result.draft_url == "draft_url"
        assert result.subtitle_url == "subtitle_url"
        assert result.video_url == "video_url"

    def test_execute_drive_batch_no_unprocessed_videos(self):
        """未処理動画がない場合のテスト"""
        self.usecase._find_unprocessed_video_from_drive = Mock(return_value=None)  # type: ignore[method-assign]

        result = self.usecase.execute_drive_batch("input_url", "output_url")

        assert result.success is True
        assert result.message == "処理対象の動画がありません"

    def test_find_unprocessed_video_from_drive(self):
        """未処理動画検出のテスト"""
        video_files = [
            DriveFile(name="video1.mp4", file_id="id1", download_url="url1", mime_type="video/mp4"),
            DriveFile(name="video2.mp4", file_id="id2", download_url="url2", mime_type="video/mp4"),
        ]
        folder = DriveFolder("folder_id", video_files)
        self.mock_google_drive_client.list_files.return_value = folder
        self.mock_google_drive_client.extract_folder_id.return_value = "output_id"
        self.mock_google_drive_client.folder_exists.side_effect = [True, False]

        result = self.usecase._find_unprocessed_video_from_drive("input_url", "output_url")

        assert result is not None
        assert result.name == "video2.mp4"

    def test_is_video_file(self):
        """動画ファイル判定のテスト"""
        video_file = DriveFile(name="test.mp4", file_id="id1", download_url="url1", mime_type="video/mp4")
        non_video_file = DriveFile(name="test.txt", file_id="id2", download_url="url2", mime_type="text/plain")

        assert self.usecase._is_video_file(video_file) is True
        assert self.usecase._is_video_file(non_video_file) is False
