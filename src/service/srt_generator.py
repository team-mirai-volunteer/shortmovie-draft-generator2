"""SRT字幕ファイル生成サービス"""

import os
from typing import Optional

from ..models.transcription import TranscriptionResult


class SrtGenerationError(Exception):
    """SRT生成関連のエラー"""

    def __init__(self, message: str, file_path: Optional[str] = None):
        super().__init__(message)
        self.file_path = file_path


class SrtGenerator:
    """SRT字幕ファイル生成サービス

    TranscriptionResultからSRT形式の字幕ファイルを生成する責務を持つ。
    時刻フォーマット変換、SRT形式の構築、ファイル出力を担当。

    Example:
        >>> generator = SrtGenerator()
        >>> file_path = generator.generate_srt_file(transcription, "output/subtitle.srt")
        >>> print(f"字幕ファイル: {file_path}")
        字幕ファイル: output/subtitle.srt
    """

    def generate_srt_file(
        self, transcription: TranscriptionResult, output_file_path: str
    ) -> str:
        """SRT字幕ファイルを生成

        Args:
            transcription: 文字起こし結果
            output_file_path: 出力ファイルパス

        Returns:
            生成されたファイルのパス

        Raises:
            SrtGenerationError: SRT生成に失敗した場合
        """
        try:
            srt_content = self.build_srt_content(transcription)

            # 出力ディレクトリが存在しない場合は作成
            output_dir = os.path.dirname(output_file_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(srt_content)

            return output_file_path

        except Exception as e:
            raise SrtGenerationError(
                f"字幕ファイルの生成に失敗しました: {str(e)}", output_file_path
            )

    def build_srt_content(self, transcription: TranscriptionResult) -> str:
        """SRT形式の内容を構築

        Args:
            transcription: 文字起こし結果

        Returns:
            SRT形式の文字列
        """
        srt_lines = []

        for i, segment in enumerate(transcription.segments, 1):
            start_time = self.format_seconds_to_srt_time(segment.start_time)
            end_time = self.format_seconds_to_srt_time(segment.end_time)

            srt_lines.extend(
                [
                    str(i),
                    f"{start_time} --> {end_time}",
                    segment.text,
                    "",
                ]
            )

        return "\n".join(srt_lines)

    def format_seconds_to_srt_time(self, seconds: float) -> str:
        """秒数をSRT形式の時刻に変換

        Args:
            seconds: 変換する秒数

        Returns:
            SRT形式の時刻文字列（hh:mm:ss,mmm）
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
