"""動画ソース関連のプロトコルとインターフェース"""

from typing import Protocol


class VideoSource(Protocol):
    """動画ソースのプロトコル

    動画ファイルの取得とクリーンアップを定義するプロトコルです。
    ローカルファイル、Google Drive、その他のソースに対応できます。

    Example:
        >>> class LocalVideoSource:
        ...     def get_video_path(self, output_dir: str) -> str:
        ...         return "/path/to/local/video.mp4"
        ...     def cleanup(self) -> None:
        ...         pass
        >>> source = LocalVideoSource()
        >>> path = source.get_video_path("output/")
        >>> print(f"動画パス: {path}")
        動画パス: /path/to/local/video.mp4
    """

    def get_video_path(self, output_dir: str) -> str:
        """動画ファイルのパスを取得（必要に応じてダウンロード）

        Args:
            output_dir: 出力ディレクトリパス

        Returns:
            動画ファイルのパス
        """
        ...

    def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        ...
