"""Google Drive公開フォルダからのファイル取得クライアント"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, List
from urllib.parse import unquote
from pathlib import Path

from ..models.drive import DriveFile, DriveFolder


class GoogleDriveError(Exception):
    """Google Drive関連のベース例外"""

    pass


class FolderAccessError(GoogleDriveError):
    """フォルダアクセスエラー"""

    def __init__(self, message: str, folder_url: str):
        super().__init__(message)
        self.folder_url = folder_url


class FileDownloadError(GoogleDriveError):
    """ファイルダウンロードエラー"""

    def __init__(self, message: str, file_name: str):
        super().__init__(message)
        self.file_name = file_name


class NoVideoFileError(GoogleDriveError):
    """動画ファイルが見つからないエラー"""

    def __init__(self, message: str, folder_url: str):
        super().__init__(message)
        self.folder_url = folder_url


class GoogleDriveClient:
    """Google Drive公開フォルダからのファイル取得クライアント

    HTMLスクレイピングによる公開フォルダアクセス（認証不要）を提供します。
    フォルダ内のファイル一覧取得、動画ファイルの自動選択、ダウンロード機能を含みます。

    Example:
        >>> client = GoogleDriveClient()
        >>> folder = client.list_files("https://drive.google.com/drive/folders/abc123?usp=sharing")
        >>> video_file = client.select_earliest_video_file(folder)
        >>> if video_file:
        ...     path = client.download_file(video_file, "output/")
        ...     print(f"ダウンロード完了: {path}")
        ダウンロード完了: output/sample_video.mp4
    """

    def __init__(self, session: Optional[requests.Session] = None):
        """GoogleDriveClientを初期化

        Args:
            session: HTTPセッション（テスト用）
        """
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; ShortMovieDraftGenerator/1.0)"})

        self.video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}

    def extract_folder_id(self, folder_url: str) -> str:
        """フォルダURLからフォルダIDを抽出

        Args:
            folder_url: Google DriveフォルダURL

        Returns:
            抽出されたフォルダID

        Raises:
            FolderAccessError: 無効なURLの場合
        """
        pattern = r"/folders/([a-zA-Z0-9_-]+)"
        match = re.search(pattern, folder_url)

        if not match:
            raise FolderAccessError(f"無効なGoogle DriveフォルダURLです: {folder_url}", folder_url)

        return match.group(1)

    def list_files(self, folder_url: str) -> DriveFolder:
        """公開フォルダのファイル一覧を取得

        Args:
            folder_url: Google DriveフォルダURL

        Returns:
            フォルダ情報（DriveFolder）

        Raises:
            FolderAccessError: フォルダアクセスに失敗した場合
        """
        try:
            folder_id = self.extract_folder_id(folder_url)

            response = self.session.get(folder_url, timeout=30)
            response.raise_for_status()

            files = self._parse_folder_html(response.text, folder_id)

            return DriveFolder(folder_id=folder_id, files=files)

        except requests.RequestException as e:
            raise FolderAccessError(f"Google Driveフォルダへのアクセスに失敗しました: {str(e)}", folder_url)
        except Exception as e:
            raise FolderAccessError(f"フォルダ情報の取得に失敗しました: {str(e)}", folder_url)

    def download_file(self, file: DriveFile, output_dir: str) -> str:
        """ファイルをダウンロード

        Args:
            file: ダウンロード対象のファイル情報
            output_dir: 出力ディレクトリパス

        Returns:
            ダウンロードされたファイルのパス

        Raises:
            FileDownloadError: ダウンロードに失敗した場合
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            file_path = output_path / file.name

            download_url = f"https://drive.google.com/uc?export=download&id={file.file_id}"

            response = self.session.get(download_url, stream=True, timeout=300)
            response.raise_for_status()

            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            return str(file_path)

        except Exception as e:
            raise FileDownloadError(f"ファイルのダウンロードに失敗しました: {str(e)}", file.name)

    def select_earliest_video_file(self, folder: DriveFolder) -> Optional[DriveFile]:
        """最も若いファイル名の動画ファイルを選択

        Args:
            folder: 検索対象のフォルダ情報

        Returns:
            選択された動画ファイル（見つからない場合はNone）
        """
        video_files = [f for f in folder.files if any(f.name.lower().endswith(ext) for ext in self.video_extensions)]

        if not video_files:
            return None

        return sorted(video_files, key=lambda f: f.name.lower())[0]

    def _parse_folder_html(self, html: str, folder_id: str) -> List[DriveFile]:
        """フォルダのHTMLからファイル情報を抽出

        Args:
            html: Google DriveフォルダのHTML
            folder_id: フォルダID

        Returns:
            抽出されたファイル情報のリスト
        """
        soup = BeautifulSoup(html, "html.parser")
        files = []

        script_tags = soup.find_all("script")
        for script in script_tags:
            script_content = getattr(script, 'string', None)
            if script_content and isinstance(script_content, str) and "file" in script_content.lower():
                file_matches = re.findall(r'"([^"]+\.(?:mp4|avi|mov|mkv|wmv|flv|webm))".*?"([a-zA-Z0-9_-]+)"', script_content, re.IGNORECASE)

                for file_name, file_id in file_matches:
                    files.append(DriveFile(name=unquote(file_name), file_id=file_id, download_url=f"https://drive.google.com/uc?export=download&id={file_id}"))

        return files
