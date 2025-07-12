"""フック関連のデータ構造"""

from dataclasses import dataclass

from .transcription import TranscriptionResult, TranscriptionSegment


@dataclass
class HookItem:
    """フック抽出結果の単一アイテム

    Attributes:
        first_hook: 最初のフック
        second_hook: 2番目のフック
        third_hook: 3番目のフック
        last_conclusion: 最後の結論
        summary: 要約

    Example:
        >>> hook = HookItem(
        ...     first_hook="え、こんな政治家見たことない！",
        ...     second_hook="あなたはこの事実、知ってましたか？",
        ...     third_hook="政治って、ほぼ宗教です。",
        ...     last_conclusion="Z世代よ、政治はただの遠い話じゃない",
        ...     summary="政治家の意外な一面を紹介",
        ... )
        >>> print(hook.summary)
        政治家の意外な一面を紹介

    """

    first_hook: str
    second_hook: str
    third_hook: str
    last_conclusion: str
    summary: str


@dataclass
class HooksExtractionResult:
    """フック抽出の全体結果

    Attributes:
        items: フックアイテムのリスト（10個）
        original_transcription: 元の文字起こし結果

    Example:
        >>> from .transcription import TranscriptionSegment, TranscriptionResult
        >>> segments = [TranscriptionSegment(0.0, 10.0, "テスト")]
        >>> transcription = TranscriptionResult(segments, "テスト")
        >>> hooks = [HookItem("hook1", "hook2", "hook3", "conclusion", "summary")]
        >>> result = HooksExtractionResult(hooks, transcription)
        >>> print(len(result.items))
        1

    """

    items: list[HookItem]
    original_transcription: TranscriptionResult


@dataclass
class DetailedScript:
    """詳細台本生成結果

    Attributes:
        hook_item: 対応するフックアイテム
        script_content: 台本内容
        duration_seconds: 想定再生時間（秒）
        segments_used: 使用されたセグメント

    Example:
        >>> hook = HookItem("hook1", "hook2", "hook3", "conclusion", "summary")
        >>> script = DetailedScript(hook_item=hook, script_content="【台本構成】\\n[00:00–00:06] ナレーション...", duration_seconds=60, segments_used=[])
        >>> print(script.duration_seconds)
        60

    """

    hook_item: HookItem
    script_content: str
    duration_seconds: int
    segments_used: list[TranscriptionSegment]


@dataclass
class TwoPhaseResult:
    """2段階処理の最終結果

    Attributes:
        hooks_result: フック抽出結果
        detailed_scripts: 詳細台本のリスト
        success: 処理成功フラグ
        error_message: エラーメッセージ（失敗時）

    Example:
        >>> from .transcription import TranscriptionSegment, TranscriptionResult
        >>> segments = [TranscriptionSegment(0.0, 10.0, "テスト")]
        >>> transcription = TranscriptionResult(segments, "テスト")
        >>> hooks = [HookItem("hook1", "hook2", "hook3", "conclusion", "summary")]
        >>> hooks_result = HooksExtractionResult(hooks, transcription)
        >>> scripts = [DetailedScript(hooks[0], "台本内容", 60, [])]
        >>> result = TwoPhaseResult(hooks_result, scripts, True)
        >>> print(result.success)
        True

    """

    hooks_result: HooksExtractionResult
    detailed_scripts: list[DetailedScript]
    success: bool
    error_message: str | None = None
