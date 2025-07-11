"""ChatGPT用プロンプト生成モジュール"""

from typing import List
from ..models.transcription import TranscriptionResult, TranscriptionSegment


class PromptBuilder:
    """ChatGPT用プロンプト生成クラス

    文字起こし結果からショート動画企画書生成用のプロンプトを構築します。
    ショート動画のベストプラクティスに基づいた5個の企画提案を生成します。

    Example:
        >>> from src.models.transcription import TranscriptionResult, TranscriptionSegment
        >>> segments = [TranscriptionSegment(0.0, 10.0, "テスト内容")]
        >>> transcription = TranscriptionResult(segments, "テスト内容")
        >>> builder = PromptBuilder()
        >>> prompt = builder.build_draft_prompt(transcription)
        >>> print(len(prompt) > 0)
        True
    """

    DRAFT_PROMPT_TEMPLATE = """# 依頼内容
以下の動画の書き起こしテキストから、切り抜き動画として適切な部分の概要を抜き出してください。

- 動画の中で話している内容に肯定的な内容になるようにしてください。
- この動画から切り抜き動画を作って面白い動画を作りたいです。
- 切り抜き動画に向いている箇所を5個ピックアップしてください。
- 1分程度の尺になるようにしてください。

# 動画書き起こし

## 全体テキスト
{full_text}

## タイムスタンプ付きセグメント
{segments_text}

# 次の点をjson形式でアウトプットとして出してください

{{
  "items": [
    {{
      "first_impact": "最初の2秒に含まれる、興味を惹くフレーズ",
      "last_conclusion": "動画の最後に来る結論。関心して終われる学び、共感できる内容、もしくは笑えるオチなど",
      "summary": "動画の主題。〇〇は〇〇なので〇〇である。ような端的な形式",
      "time_start": "開始時刻(hh:mm:ss)",
      "time_end": "終了時刻(hh:mm:ss)",
      "title": "魅力的なタイトル（30文字以内）",
      "caption": "SNS投稿用キャプション（100文字以内、ハッシュタグ含む）",
      "key_points": [
        "重要なポイント1",
        "重要なポイント2",
        "重要なポイント3"
      ]
    }},
    ...
  ]
}}

# ショート動画を作る主なポイントは以下の通りです。

## 冒頭2秒でインパクトを出す
* 冒頭の2秒はユーザーとの**最初の接点**であり、短い動画においては非常に大きい時間です。
* 基本的にフォロワー以外の動画が見られることが多いため、投稿者は**通りすがりの人**という認識を持つ必要があります。
* 通りすがりの人に丁寧な挨拶は不要であり、それよりも最初の数秒で「面白い」と思わせないと**スクロールされて消えていく**ため、**勝負にならない**とされています。
* バズった動画を分析した結果、伸びている動画の**9割はファーストビューを意識している**とのことです。
* 冒頭の2秒はYouTubeでいう**サムネイル**のようなもの

## 視聴時間をハックする（伸ばす）
* アルゴリズムの**7割が視聴時間**に関わっていると考えています。
* 個人的なデータとして、再生数と平均視聴時間にフル視聴率を掛け算した値は相関関係にあり、**すべては視聴時間に行き着く**とのことです。
* 「いいね！」やコメント率、シェア率よりも、**視聴時間の指標を重要視した方がバズる確率が高い**と述べています。
* 視聴時間を伸ばすためには、冒頭の2秒（サムネイル部分）以降の3秒目以降で**ユーザーが離脱しない内容**にする必要があります。
* ユーザーを**飽きさせない展開**を作り続けるのがコツです。
* トルコアイスの動画がお客を飽きさせない仕掛けを次々と繰り出すように、動画も5〜10秒程度で話を切り替えたり、色々なカットを使ったりする といった工夫が、視聴者を飽きさせないために有効だとされています。
* 終盤は視聴時間への寄与は少ないものの、最後に**共感や感動、オチ**などがあればユーザーの満足度が上がると考えられています。

JSON形式以外の出力は一切含めず、上記形式で正確に回答してください。
"""

    def build_draft_prompt(self, transcription: TranscriptionResult) -> str:
        """文字起こし結果からショート動画企画書生成用プロンプトを構築

        Args:
            transcription: 文字起こし結果

        Returns:
            ChatGPT APIに送信するプロンプト文字列

        Raises:
            ValueError: transcriptionが無効な場合
        """
        self._validate_transcription(transcription)

        segments_text = self._format_segments(transcription.segments)

        prompt = self.DRAFT_PROMPT_TEMPLATE.format(full_text=transcription.full_text, segments_text=segments_text)
        print(prompt)
        return prompt

    def _format_time_to_hms(self, seconds: float) -> str:
        """秒数をhh:mm:ss形式に変換

        Args:
            seconds: 変換する秒数

        Returns:
            hh:mm:ss形式の時刻文字列
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _format_segments(self, segments: List[TranscriptionSegment]) -> str:
        """セグメント情報を読みやすい形式にフォーマット

        Args:
            segments: フォーマットするセグメントのリスト

        Returns:
            フォーマットされたセグメント文字列
        """
        formatted_lines = []
        for i, segment in enumerate(segments, 1):
            start_time = self._format_time_to_hms(segment.start_time)
            end_time = self._format_time_to_hms(segment.end_time)

            time_range = f"[{start_time} - {end_time}]"
            formatted_lines.append(f"{i:3d}. {time_range} {segment.text}")

        return "\n".join(formatted_lines)

    def _validate_transcription(self, transcription: TranscriptionResult) -> None:
        """文字起こし結果の妥当性をチェック

        Args:
            transcription: 検証する文字起こし結果

        Raises:
            ValueError: transcriptionが無効な場合
        """
        if not transcription.segments:
            raise ValueError("セグメントが空です")
        if not transcription.full_text.strip():
            raise ValueError("全体テキストが空です")
