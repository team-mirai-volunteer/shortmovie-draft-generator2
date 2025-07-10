"""Google Drive API v3 サービスアカウント認証クライアント"""

import os
import json
from typing import Optional, List
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

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


class GoogleDriveAPIError(GoogleDriveError):
    """Google Drive API関連のエラー"""

    def __init__(self, message: str, api_error_code: Optional[str] = None):
        super().__init__(message)
        self.api_error_code = api_error_code


class APIKeyError(GoogleDriveError):
    """APIキー関連のエラー"""

    def __init__(self, message: str):
        super().__init__(message)


class QuotaExceededError(GoogleDriveError):
    """API使用量制限エラー"""

    def __init__(self, message: str):
        super().__init__(message)


class GoogleDriveClient:
    """Google Drive API v3 サービスアカウント認証クライアント

    サービスアカウントを使用して共有フォルダからファイル情報を取得します。
    フォルダの公開設定を変更せず、サービスアカウントに共有権限を付与するだけで使用可能です。

    Example:
        >>> client = GoogleDriveClient(service_account_path="path/to/service-account.json")
        >>> folder = client.list_files("https://drive.google.com/drive/folders/abc123?usp=sharing")
        >>> video_file = client.select_earliest_video_file(folder)
        >>> if video_file:
        ...     path = client.download_file(video_file, "output/")
        ...     print(f"ダウンロード完了: {path}")
        ダウンロード完了: output/sample_video.mp4
    """

    def __init__(self, service_account_path: str):
        """GoogleDriveClientを初期化

        Args:
            service_account_path: サービスアカウントキーファイルのパス
        """
        self.service_account_path = service_account_path
        # 読み取りとアップロード両方に対応するスコープ
        self.scopes = ['https://www.googleapis.com/auth/drive']

        # サポートする動画ファイル拡張子
        self.video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}

        # 動画ファイルのMIMEタイプ
        self.video_mime_types = {
            "video/mp4",
            "video/avi",
            "video/quicktime",
            "video/x-msvideo",
            "video/x-ms-wmv",
            "video/x-flv",
            "video/webm"
        }

        # Google Drive APIサービスを初期化
        self.service = self._build_service()

    def _build_service(self):
        """Google Drive APIサービスを構築"""
        try:
            # サービスアカウントキーファイルから認証情報を読み込み
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_path,
                scopes=self.scopes
            )

            # Google Drive APIサービスを構築
            service = build('drive', 'v3', credentials=credentials)
            return service

        except FileNotFoundError:
            raise GoogleDriveError(f"サービスアカウントキーファイルが見つかりません: {self.service_account_path}")
        except json.JSONDecodeError:
            raise GoogleDriveError(f"サービスアカウントキーファイルの形式が正しくありません: {self.service_account_path}")
        except Exception as e:
            raise GoogleDriveError(f"Google Drive APIサービスの初期化に失敗しました: {str(e)}")

    def extract_folder_id(self, folder_url: str) -> str:
        """フォルダURLからフォルダIDを抽出

        Args:
            folder_url: Google DriveフォルダURL

        Returns:
            抽出されたフォルダID

        Raises:
            FolderAccessError: 無効なURLの場合
        """
        try:
            if "/folders/" in folder_url:
                folder_id = folder_url.split("/folders/")[1].split("?")[0].split("/")[0]
                return folder_id
            else:
                raise FolderAccessError(f"無効なGoogle DriveフォルダURLです: {folder_url}", folder_url)
        except Exception as e:
            raise FolderAccessError(f"フォルダIDの抽出に失敗しました: {str(e)}", folder_url)

    def list_files(self, folder_url: str) -> DriveFolder:
        """共有フォルダのファイル一覧を取得

        Args:
            folder_url: Google DriveフォルダURL

        Returns:
            フォルダ情報（DriveFolder）

        Raises:
            FolderAccessError: フォルダアクセスに失敗した場合
        """
        try:
            folder_id = self.extract_folder_id(folder_url)

            # フォルダ詳細取得をスキップして、直接ファイル一覧取得を試行
            print(f"DEBUG: フォルダID: {folder_id}")
            print(f"DEBUG: サービスアカウント: {self._get_service_account_email()}")

            # フォルダ内のファイル一覧を取得
            try:
                query = f"'{folder_id}' in parents and trashed=false"
                print(f"DEBUG: クエリ: {query}")

                results = self.service.files().list(
                    q=query,
                    fields="files(id,name,mimeType,size,webContentLink)"
                ).execute()

                files_data = results.get('files', [])

                # デバッグ用: 取得したファイル一覧を表示
                print(f"DEBUG: フォルダ内のファイル数: {len(files_data)}")
                for file_data in files_data:
                    print(f"DEBUG: ファイル名: {file_data.get('name', 'N/A')}, MIMEタイプ: {file_data.get('mimeType', 'N/A')}")

                files = self._parse_api_response(files_data)

                print(f"DEBUG: 動画ファイルとして認識されたファイル数: {len(files)}")
                for file in files:
                    print(f"DEBUG: 動画ファイル: {file.name}")

                return DriveFolder(folder_id=folder_id, files=files)

            except Exception as e:
                print(f"DEBUG: ファイル一覧取得エラー: {str(e)}")
                raise FolderAccessError(
                    f"フォルダ内のファイル一覧取得に失敗しました。サービスアカウント（{self._get_service_account_email()}）に"
                    f"フォルダの共有権限が付与されているか確認してください。\n"
                    f"Google Driveでフォルダを右クリック → 共有 → サービスアカウントのメールアドレスを追加してください。\n"
                    f"エラー詳細: {str(e)}",
                    folder_url
                )

        except FolderAccessError:
            raise
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

            # Google Drive APIでファイルをダウンロード
            request = self.service.files().get_media(fileId=file.file_id)

            with open(file_path, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    if status:
                        print(f"DEBUG: ダウンロード進行状況: {int(status.progress() * 100)}%")

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
        video_files = [
            f for f in folder.files
            if any(f.name.lower().endswith(ext) for ext in self.video_extensions)
        ]

        if not video_files:
            return None

        # ファイル名でソート（アルファベット順、大文字小文字を区別しない）
        return sorted(video_files, key=lambda f: f.name.lower())[0]

    def _parse_api_response(self, files_data: List[dict]) -> List[DriveFile]:
        """Google Drive APIレスポンスからファイル情報を抽出

        Args:
            files_data: APIから取得したファイルデータのリスト

        Returns:
            DriveFileオブジェクトのリスト
        """
        files = []

        for file_data in files_data:
            # 動画ファイルのみを対象とする
            mime_type = file_data.get("mimeType", "")
            file_name = file_data.get("name", "")

            is_video = (
                any(file_name.lower().endswith(ext) for ext in self.video_extensions) or
                mime_type in self.video_mime_types
            )

            if is_video:
                files.append(DriveFile(
                    name=file_name,
                    file_id=file_data["id"],
                    download_url=f"https://drive.google.com/uc?export=download&id={file_data['id']}",
                    size=int(file_data.get("size", 0)) if file_data.get("size") else None
                ))

        return files

    def _get_service_account_email(self) -> str:
        """サービスアカウントのメールアドレスを取得"""
        try:
            with open(self.service_account_path, 'r') as f:
                service_account_info = json.load(f)
                return service_account_info.get('client_email', 'unknown')
        except:
            return 'unknown'
