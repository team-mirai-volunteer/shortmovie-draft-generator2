"""Google Drive動画ソースの実装"""

from typing import Optional
from ..clients.google_drive_client import GoogleDriveClient, NoVideoFileError


class GoogleDriveVideoSource:
    """Google Driveソース

    Google Driveの公開フォルダから動画ファイルを取得するVideoSourceの実装です。
    フォルダ内の最も若いファイル名の動画ファイルを自動選択してダウンロードします。

    Example:
        >>> from ..clients.google_drive_client import GoogleDriveClient
        >>> client = GoogleDriveClient()
        >>> source = GoogleDriveVideoSource(
        ...     "https://drive.google.com/drive/folders/abc123?usp=sharing",
        ...     client
        ... )
        >>> path = source.get_video_path("output/")
        >>> print(f"ダウンロード済み動画: {path}")
        ダウンロード済み動画: output/sample_video.mp4
    """

    def __init__(self, folder_url: str, drive_client: GoogleDriveClient):
        """GoogleDriveVideoSourceを初期化

        Args:
            folder_url: Google DriveフォルダURL
            drive_client: Google Driveクライアント
        """
        self.folder_url = folder_url
        self.drive_client = drive_client
        self.downloaded_file_path: Optional[str] = None

    def get_video_path(self, output_dir: str) -> str:
        """Google Driveから動画ファイルをダウンロードしてパスを返す

        Args:
            output_dir: 出力ディレクトリパス

        Returns:
            ダウンロードされた動画ファイルのパス

        Raises:
            NoVideoFileError: フォルダ内に動画ファイルが見つからない場合
        """
        folder = self.drive_client.list_files(self.folder_url)

        video_file = self.drive_client.select_earliest_video_file(folder)

        if not video_file:
            raise NoVideoFileError("フォルダ内に動画ファイルが見つかりません", self.folder_url)

        downloaded_path = self.drive_client.download_file(video_file, output_dir)
        self.downloaded_file_path = downloaded_path

        return downloaded_path

    def cleanup(self) -> None:
        """ダウンロードしたファイルの削除（オプション）

        現在の要件では削除しないため、何も実行しません。
        """
        pass
