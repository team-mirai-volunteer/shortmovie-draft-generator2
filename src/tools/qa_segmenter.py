"""質問回答セグメント抽出ツール"""

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class QuestionSegment:
    """質問セグメント"""

    text: str
    start_time: float
    end_time: float
    speaker: str | None = None


@dataclass
class AnswerSegment:
    """回答セグメント"""

    text: str
    start_time: float
    end_time: float


@dataclass
class QASegment:
    """質問回答ペア"""

    id: int
    question: QuestionSegment
    answer: AnswerSegment
    total_duration: float

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "question": {
                "text": self.question.text,
                "start_time": self.question.start_time,
                "end_time": self.question.end_time,
                "speaker": self.question.speaker,
            },
            "answer": {
                "text": self.answer.text,
                "start_time": self.answer.start_time,
                "end_time": self.answer.end_time,
            },
            "total_duration": self.total_duration,
        }


class QASegmenterError(Exception):
    """QASegmenter関連のベース例外"""


class QASegmenter:
    """質問回答セグメント抽出器

    Whisper文字起こしデータから質問回答ペアを特定し、
    指定された数のセグメントを抽出します。
    """

    def __init__(self):
        """QASegmenterを初期化"""
        self.question_patterns = [
            r"次は、(.+?)さんからの質問です",
            r"(.+?)さんからのご質問です",
            r"(.+?)さん、お質問ありがとう",
            r"(.+?)からのご質問",
        ]

        self.transition_patterns = [
            r"^次は、",
            r"^ありがとう",
            r"^では、",
            r"^それでは",
        ]

    def extract_qa_segments(
        self, transcription_data: dict[str, Any], num_segments: int = 3
    ) -> list[QASegment]:
        """文字起こしデータからQ&Aセグメントを抽出

        Args:
            transcription_data: Whisper APIからの文字起こしデータ
            num_segments: 抽出するセグメント数

        Returns:
            抽出されたQ&Aセグメントのリスト

        Raises:
            QASegmenterError: セグメント抽出に失敗した場合
        
        """
        try:
            segments = transcription_data.get("segments", [])
            if not segments:
                raise QASegmenterError("セグメントデータが見つかりません")

            question_markers = self._find_question_markers(segments)

            if len(question_markers) < num_segments:
                raise QASegmenterError(
                    f"十分な質問セグメントが見つかりません。要求: {num_segments}, 発見: {len(question_markers)}"
                )

            selected_questions = self._select_distributed_questions(
                question_markers, num_segments
            )

            qa_segments = []
            for i, question_info in enumerate(selected_questions):
                qa_segment = self._extract_single_qa(
                    segments, question_info, i + 1, selected_questions
                )
                if qa_segment:
                    qa_segments.append(qa_segment)

            return qa_segments

        except Exception as e:
            raise QASegmenterError(
                f"Q&Aセグメント抽出中にエラーが発生しました: {e!s}"
            ) from e

    def _find_question_markers(
        self, segments: list[dict[str, Any]]
    ) -> list[tuple[int, dict[str, Any], str]]:
        """質問マーカーを検出

        Returns:
            (セグメントインデックス, セグメントデータ, 質問者名) のタプルリスト
        
        """
        question_markers = []

        for i, segment in enumerate(segments):
            text = segment.get("text", "").strip()

            for pattern in self.question_patterns:
                match = re.search(pattern, text)
                if match:
                    speaker = match.group(1) if match.groups() else None
                    question_markers.append((i, segment, speaker))
                    break

        return question_markers

    def _select_distributed_questions(
        self, question_markers: list[tuple[int, dict[str, Any], str]], num_segments: int
    ) -> list[tuple[int, dict[str, Any], str]]:
        """時間的に分散した質問を選択"""
        if len(question_markers) <= num_segments:
            return question_markers

        total_questions = len(question_markers)
        step = total_questions // num_segments

        selected = []
        for i in range(num_segments):
            index = i * step
            if i == num_segments - 1:  # 最後は末尾から選択
                index = total_questions - 1
            selected.append(question_markers[index])

        return selected

    def _extract_single_qa(
        self,
        segments: list[dict[str, Any]],
        question_info: tuple[int, dict[str, Any], str],
        qa_id: int,
        all_selected_questions: list[tuple[int, dict[str, Any], str]],
    ) -> QASegment | None:
        """単一のQ&Aセグメントを抽出"""
        question_idx, question_segment, speaker = question_info

        question_end_idx = self._find_question_end(segments, question_idx)

        answer_end_idx = self._find_answer_end(
            segments, question_end_idx, all_selected_questions
        )

        question_text = self._build_text_range(segments, question_idx, question_end_idx)
        question_start = segments[question_idx]["start"]
        question_end = segments[question_end_idx]["end"]

        answer_text = self._build_text_range(
            segments, question_end_idx + 1, answer_end_idx
        )
        answer_start = (
            segments[question_end_idx + 1]["start"]
            if question_end_idx + 1 < len(segments)
            else question_end
        )
        answer_end = (
            segments[answer_end_idx]["end"]
            if answer_end_idx < len(segments)
            else answer_start
        )

        if not answer_text.strip():
            return None

        question_seg = QuestionSegment(
            text=question_text.strip(),
            start_time=float(question_start),
            end_time=float(question_end),
            speaker=speaker,
        )

        answer_seg = AnswerSegment(
            text=answer_text.strip(),
            start_time=float(answer_start),
            end_time=float(answer_end),
        )

        total_duration = float(answer_end) - float(question_start)

        return QASegment(
            id=qa_id,
            question=question_seg,
            answer=answer_seg,
            total_duration=total_duration,
        )

    def _find_question_end(
        self, segments: list[dict[str, Any]], question_start_idx: int
    ) -> int:
        """質問の終了位置を特定"""
        for i in range(question_start_idx, min(question_start_idx + 5, len(segments))):
            text = segments[i].get("text", "")
            if "？" in text or "?" in text:
                return i

        return min(question_start_idx + 1, len(segments) - 1)

    def _find_answer_end(
        self,
        segments: list[dict[str, Any]],
        answer_start_idx: int,
        all_questions: list[tuple[int, dict[str, Any], str]],
    ) -> int:
        """回答の終了位置を特定"""
        next_question_idx = None
        for q_idx, _, _ in all_questions:
            if q_idx > answer_start_idx:
                next_question_idx = q_idx
                break

        if next_question_idx is not None:
            return next_question_idx - 1

        for i in range(answer_start_idx + 1, len(segments)):
            text = segments[i].get("text", "").strip()
            for pattern in self.transition_patterns:
                if re.match(pattern, text):
                    return i - 1

        return len(segments) - 1

    def _build_text_range(
        self, segments: list[dict[str, Any]], start_idx: int, end_idx: int
    ) -> str:
        """指定範囲のセグメントからテキストを構築"""
        texts = []
        for i in range(start_idx, min(end_idx + 1, len(segments))):
            text = segments[i].get("text", "").strip()
            if text:
                texts.append(text)
        return "".join(texts)

    def format_time_to_hms(self, seconds: float) -> str:
        """秒数をhh:mm:ss形式に変換"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
