"""Google Drive関連のデータ構造"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DriveFile:
    """Google Driveファイル情報

    Attributes:
        name: ファイル名
        file_id: Google DriveファイルID
        download_url: ダウンロード用URL
        size: ファイルサイズ（バイト）

    Example:
        >>> drive_file = DriveFile(
        ...     name="sample_video.mp4",
        ...     file_id="1abc123def456",
        ...     download_url="https://drive.google.com/uc?export=download&id=1abc123def456",
        ...     size=1024000
        ... )
        >>> print(f"ファイル名: {drive_file.name}")
        ファイル名: sample_video.mp4
    """

    name: str
    file_id: str
    download_url: str
    size: Optional[int] = None


@dataclass
class DriveFolder:
    """Google Driveフォルダ情報

    Attributes:
        folder_id: Google DriveフォルダID
        files: フォルダ内のファイルリスト

    Example:
        >>> files = [
        ...     DriveFile("video1.mp4", "1abc123", "https://...", 1024),
        ...     DriveFile("video2.mp4", "2def456", "https://...", 2048)
        ... ]
        >>> folder = DriveFolder("folder123", files)
        >>> print(f"ファイル数: {len(folder.files)}")
        ファイル数: 2
    """

    folder_id: str
    files: List[DriveFile]
