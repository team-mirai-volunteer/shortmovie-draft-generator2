"""Google Drive API v3 サービスアカウント認証クライアント"""

import json
from typing import Optional, List, Any
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import mimetypes

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


class FileUploadError(GoogleDriveError):
    """ファイルアップロードエラー"""

    def __init__(self, message: str, file_path: str):
        super().__init__(message)
        self.file_path = file_path


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
        self.scopes = ["https://www.googleapis.com/auth/drive.file"]

        # サポートする動画ファイル拡張子
        self.video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}

        # 動画ファイルのMIMEタイプ
        self.video_mime_types = {"video/mp4", "video/avi", "video/quicktime", "video/x-msvideo", "video/x-ms-wmv", "video/x-flv", "video/webm"}

        # Google Drive APIサービスを初期化
        self.service = self._build_service()

    def _build_service(self) -> Any:
        """Google Drive APIサービスを構築"""
        try:
            # サービスアカウントキーファイルから認証情報を読み込み
            credentials = service_account.Credentials.from_service_account_file(self.service_account_path, scopes=self.scopes)

            # Google Drive APIサービスを構築
            service = build("drive", "v3", credentials=credentials)
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
                # URLを分解してIDを抽出
                parts = folder_url.split("/folders/")[1]

                # ?やその他のパラメータを除去
                folder_id = parts.split("?")[0].split("/")[0].split("#")[0]

                # IDの妥当性チェック（Google DriveのIDは通常33文字程度）
                if len(folder_id) < 20 or len(folder_id) > 50:
                    raise FolderAccessError(f"抽出されたフォルダIDが無効です: {folder_id} (長さ: {len(folder_id)})", folder_url)

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

            # まずフォルダ自体の情報を取得してアクセス可能かテスト
            try:
                folder_info = self.service.files().get(fileId=folder_id, supportsAllDrives=True).execute()
                print(f"DEBUG: フォルダ名: {folder_info.get('name', 'N/A')}")
            except Exception as e:
                raise FolderAccessError(
                    f"フォルダにアクセスできません。サービスアカウント（{self._get_service_account_email()}）に"
                    f"フォルダの共有権限が付与されているか確認してください。\n"
                    f"Google Driveでフォルダを右クリック → 共有 → サービスアカウントのメールアドレスを追加してください。\n"
                    f"エラー詳細: {str(e)}",
                    folder_url,
                )

            # フォルダ内のファイル一覧を取得
            try:
                # フォルダ内のファイル一覧を取得
                query = f"'{folder_id}' in parents and trashed=false"

                results = (
                    self.service.files()
                    .list(q=query, fields="files(id,name,mimeType,size,webContentLink)", pageSize=1000, supportsAllDrives=True, includeItemsFromAllDrives=True)
                    .execute()
                )

                files_data = results.get("files", [])

                # ファイルが見つからない場合、代替クエリを試行
                if len(files_data) == 0:
                    print("DEBUG: 基本クエリでファイルが見つからないため、代替クエリを試行...")

                    # 代替クエリ: trashedの条件を外す
                    alt_query = f"'{folder_id}' in parents"
                    alt_results = (
                        self.service.files()
                        .list(
                            q=alt_query,
                            fields="files(id,name,mimeType,size,webContentLink)",
                            pageSize=1000,
                            supportsAllDrives=True,
                            includeItemsFromAllDrives=True,
                        )
                        .execute()
                    )

                    files_data = alt_results.get("files", [])

                files = self._parse_api_response(files_data)

                print(f"DEBUG: 動画ファイルとして認識されたファイル数: {len(files)}")

                return DriveFolder(folder_id=folder_id, files=files)

            except Exception as e:
                raise FolderAccessError(
                    f"フォルダ内のファイル一覧取得に失敗しました。サービスアカウント（{self._get_service_account_email()}）に"
                    f"フォルダの共有権限が付与されているか確認してください。\n"
                    f"Google Driveでフォルダを右クリック → 共有 → サービスアカウントのメールアドレスを追加してください。\n"
                    f"エラー詳細: {str(e)}",
                    folder_url,
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
            request = self.service.files().get_media(fileId=file.file_id, supportsAllDrives=True)

            with open(file_path, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        # 25%刻みで進行状況を表示
                        if progress % 25 == 0:
                            print(f"DEBUG: ダウンロード進行状況: {progress}%")

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

            is_video = any(file_name.lower().endswith(ext) for ext in self.video_extensions) or mime_type in self.video_mime_types

            if is_video:
                files.append(
                    DriveFile(
                        name=file_name,
                        file_id=file_data["id"],
                        download_url=f"https://drive.google.com/uc?export=download&id={file_data['id']}",
                        size=int(file_data.get("size", 0)) if file_data.get("size") else None,
                    )
                )

        return files

    def upload_file(self, file_path: str, folder_id: str, file_name: Optional[str] = None) -> str:
        """ファイルをGoogle Driveにアップロード

        Args:
            file_path: アップロード対象のファイルパス
            folder_id: アップロード先のフォルダID
            file_name: アップロード後のファイル名（省略時は元のファイル名を使用）

        Returns:
            アップロードされたファイルのGoogle Drive URL

        Raises:
            FileUploadError: アップロードに失敗した場合
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileUploadError(f"アップロード対象のファイルが見つかりません: {file_path}", file_path)

            upload_file_name = file_name or file_path_obj.name

            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = "application/octet-stream"

            file_metadata = {"name": upload_file_name, "parents": [folder_id]}

            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

            print(f"DEBUG: ファイルアップロード開始: {upload_file_name}")

            request = self.service.files().create(body=file_metadata, media_body=media, fields="id,webViewLink", supportsAllDrives=True)

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    if progress % 25 == 0:
                        print(f"DEBUG: アップロード進行状況: {progress}%")

            file_id = response.get("id")
            web_view_link = response.get("webViewLink")

            print(f"DEBUG: アップロード完了: {upload_file_name} (ID: {file_id})")

            if web_view_link:
                return web_view_link
            else:
                raise FileUploadError("アップロード後のURLが取得できませんでした", file_path)

        except FileUploadError:
            raise
        except Exception as e:
            raise FileUploadError(f"ファイルのアップロードに失敗しました: {str(e)}", file_path)

    def create_folder(self, folder_name: str, parent_folder_id: str) -> str:
        """Google Driveにフォルダを作成

        Args:
            folder_name: 作成するフォルダ名
            parent_folder_id: 親フォルダのID

        Returns:
            作成されたフォルダのID

        Raises:
            GoogleDriveError: フォルダ作成に失敗した場合
        """
        try:
            file_metadata = {"name": folder_name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_folder_id]}

            folder = self.service.files().create(body=file_metadata, fields="id", supportsAllDrives=True).execute()

            folder_id = folder.get("id")
            print(f"DEBUG: フォルダ作成完了: {folder_name} (ID: {folder_id})")

            if folder_id:
                return folder_id
            else:
                raise GoogleDriveError("フォルダ作成後のIDが取得できませんでした")

        except Exception as e:
            raise GoogleDriveError(f"フォルダの作成に失敗しました: {str(e)}")

    def _get_service_account_email(self) -> str:
        """サービスアカウントのメールアドレスを取得"""
        try:
            with open(self.service_account_path, "r") as f:
                service_account_info = json.load(f)
                email = service_account_info.get('client_email')
                return str(email) if email is not None else 'unknown'
        except:
            return 'unknown'
