"""ChatGPT用プロンプト生成モジュール"""

from ..models.hooks import HookItem
from ..models.transcription import TranscriptionResult, TranscriptionSegment


class PromptBuilder:
    """ChatGPT用プロンプト生成クラス（2段階対応版）

    文字起こし結果からショート動画企画書生成用のプロンプトを構築します。
    2段階処理（フック抽出→詳細台本作成）に対応しています。

    Example:
        >>> from src.models.transcription import TranscriptionResult, TranscriptionSegment
        >>> segments = [TranscriptionSegment(0.0, 10.0, "テスト内容")]
        >>> transcription = TranscriptionResult(segments, "テスト内容")
        >>> builder = PromptBuilder()
        >>> hooks_prompt = builder.build_hooks_prompt(transcription)
        >>> print(len(hooks_prompt) > 0)
        True

    """

    # フック抽出用プロンプトテンプレート
    HOOKS_PROMPT_TEMPLATE = """# 依頼内容
以下の動画の書き起こしテキストから、切り抜き動画として適切なフックとなる要素を導出してください。

# ターゲット層：Z世代（10〜20代）

# 前提
- 動画の中で話している内容に切り抜き箇所は、以下のいずれかに当てはまることが望ましい：
- 登場人物の感情（驚き、怒り、笑い、感動など）が強く出ている場面
- ストーリー性・変化・結論・主張が明快な場面
- 特定の価値観・信念・メッセージが一言で表現できる場面
- 切り抜き動画に向いている箇所を **10個**ピックアップしてください。
- 各クリップの長さは **約 1 分**を目安にしてください。
- この動画から切り抜き動画を作って **面白い**作品にしたいです。
- 絵文字は多く使用してください。
- ショート動画バズのコツは、視聴者を冒頭で惹きつける強烈なフックです、フックを意識してください。

# フックを作るための TIPS
- 1.驚きで惹きつける（Surprise）
- 例：「え、こんな政治家見たことない！」
- 理由：予想外の展開・人物像を予感させることで、続きを見たくなる。

- 2.問いかけで参加させる（Question）
- 例：「あなたはこの事実、知ってましたか？」
- 理由：視聴者に内心で"答えさせる"ことで当事者意識を生み出す。

- 3.極端な言い切りで目を引く（Bold Claim）
- 例：「政治って、ほぼ宗教です。」
- 理由：刺激的な主張が「本当に？」という好奇心を引き出す。

- 4.ギャップや矛盾を提示する（Contradiction / Tension）
- 例：「AI推進派の彼が、実は"反対派"だった理由とは」
- 理由：「一見正反対」に見える事実を並べることで、続きが気になる構造になる。

- 5.感情ワードを先出しする（Emotion First）
- 例：「怒りを覚えた出来事」
- 理由：感情を先に出すと、共感や興味が起点になりやすい。

- 6.カウントダウン/リスト構造で視認性UP（Numbered List）
- 例：「政治家のヤバい発言トップ3」
- 理由：数字が入ると「何が1位なのか？」と最後まで見たくなる。

- 7.キーワードに視覚的インパクトを入れる（Visual Word）
- 例：「年収300万円で"議員"ってどういうこと？」
- 理由：「数字」や「肩書き」などを冒頭に入れると注目が集まりやすい。

- 8.ターゲット特定型（If you're __）
- 例：「20代で政治に興味ない人、ちょっと来て」
- 理由：「これは自分向けの動画だ」と感じさせると離脱率が減る。

- 9.タイムプレッシャー／今だけ要素（Urgency）
- 例：「この制度、来月から変わります」
- 理由：すぐに知っておかないと損する感覚を植え付ける。

- 10.シーン説明＋謎かけ（Narrative Hook）
- 例：「居酒屋で突然"あの話"が始まった」
- 理由：ストーリー性の入り口と"何の話？"という謎を同時に

# 出力フォーマット
{{
  "items": [
    {{
      "first_hook": "",
      "second_hook": "",
      "third_hook": "",
      "summary": ""
    }},
    ...
  ]
}}"""

    # 詳細台本作成用プロンプトテンプレート
    SCRIPT_PROMPT_TEMPLATE = """# ショート動画台本作成プロンプト（本人発言のみ）

あなたは動画編集者のために、Z世代向けショート動画の台本を構成するプロフェッショナルです。
以下の `item` 情報と `segments`（タイムスタンプ付き文字起こし）をもとに、**1分以内の動画構成案**を出力してください。

---

## 入力

- `item`: {{ITEM_PLACEHOLDER}}

- `segments`: {{SEGMENTS_PLACEHOLDER}}

---

## 出力条件

1. 台本全体は**60秒以内**にしてください。
2. **first_hook**は、冒頭にテロップで使用してください。
3. **segmentsの中から発言を4~5個抽出**し、本人発言パートとして使用してください。
4. セリフは整える程度の編集（口語・つなぎ）をOKとしつつ、**本人らしさは残してください**。
5. 各発言の秒数を目安として記載してください（編集の参考に）。

---

## 注意事項
- 「**」による太字表記は使わないでください
- 台本の一番はじめの言葉は、フックと直接関係のある、興味をひく発言にしてください。
- 台本の一番はじめの言葉として、「どうもこんにちは」「アンナタカヒロです。」のようなものは絶対に使わないようにしてください。
- 台本の順序は、実際の中身と前後しても問題ありません。
- 台本構成には、おおまかな秒数を抜き出す形で記載してください。
- 一番最後の発言は、動画内での順序を大胆に無視していいので、結論として締まるものか、オチとして面白いものを選んでください。

---

## 出力形式
【フック】
🎨「作画が同じ夫婦⁉️」

【台本構成】
00:00.00 xxxxxxxxxxxxx
00:00.00 xxxxxxxxxxxxx
...

----

【台本構成例1】
08:45.12 かなりニューウェーブだから
09:03.37 若者が新しい文脈で何かをやることによって
09:03.12 その形が多少間違ってたことがあったり、拙かったとしても
09:03.09 新陳代謝するんだから意味がある
01:30.75 既存の政党に入るんじゃなくて新しい政党を立ち上げてみんな若いって
01:30.18 超反骨精神あるじゃないですか
03:40.74 どうするとブランドが立つんだろうなあ
04:46.92 取り巻く人をエッジにしていくことによって
04:46.16 自分たちをより浮かび上がらせていくみたいな
04:24.47 それだ！
04:24.75 ゆとりくんのような個性的な人が応援しているのか
47:34.66 まじ参考になるアドバイスでした

【台本構成例2】
0:31.12	米の値段、1年で2倍に！？
0:19.37	米価格問題×IT
1:58.12 お米がつくれなかった年じゃない
3:52.09	理由がわかってない状況をいち早く解決する
3:59.75	コメの見える化をITでやる
9:19.18	社会問題にはITを使って解決できるものが沢山ある
9:37.33	ぜひサポーター（ボランティア）登録お願いします

"""

    def __init__(self) -> None:
        """プロンプトテンプレートを初期化"""

    def build_hooks_prompt(self, transcription: TranscriptionResult) -> str:
        """フック抽出用プロンプトを構築

        Args:
            transcription: 文字起こし結果

        Returns:
            フック抽出用プロンプト

        """
        self._validate_transcription(transcription)

        # セグメント情報をフォーマット
        segments_text = self._format_segments(transcription.segments)

        # テンプレートに文字起こし情報を埋め込み
        prompt = (
            self.HOOKS_PROMPT_TEMPLATE
            + f"""

# 動画書き起こし

## 全体テキスト
{transcription.full_text}

## タイムスタンプ付きセグメント
{segments_text}
"""
        )

        return prompt

    def build_script_prompt(self, hook_item: HookItem, segments: list[TranscriptionSegment]) -> str:
        """詳細台本作成用プロンプトを構築

        Args:
            hook_item: フック情報
            segments: 文字起こしセグメント

        Returns:
            詳細台本作成用プロンプト

        Note:
            SCRIPT_PROMPT_TEMPLATEの`{{ITEM_PLACEHOLDER}}`と`{{SEGMENTS_PLACEHOLDER}}`を
            実際のデータで置換する

        """
        # フック情報をJSON形式で整形
        item_json = f"""{{
    "first_hook": "{self._escape_json_string(hook_item.first_hook)}",
    "second_hook": "{self._escape_json_string(hook_item.second_hook)}",
    "third_hook": "{self._escape_json_string(hook_item.third_hook)}",
    "summary": "{self._escape_json_string(hook_item.summary)}"
}}"""

        # セグメント情報を簡潔なフォーマットで整形
        segments_text = ""
        for segment in segments:
            # 開始時刻を分:秒.小数点形式に変換
            start_time_formatted = self._format_time_to_minutes_seconds(segment.start_time)
            segments_text += f"{start_time_formatted} {segment.text}\n"
        segments_text = segments_text.rstrip("\n")

        # テンプレートのプレースホルダーを置換
        prompt = self.SCRIPT_PROMPT_TEMPLATE

        # プレースホルダーを置換
        prompt = prompt.replace("{{ITEM_PLACEHOLDER}}", item_json)
        prompt = prompt.replace("{{SEGMENTS_PLACEHOLDER}}", segments_text)
        print(prompt)

        return prompt

    def _escape_json_string(self, text: str) -> str:
        """JSON文字列用のエスケープ処理

        Args:
            text: エスケープする文字列

        Returns:
            エスケープされた文字列

        """
        return text.replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")

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

    def _format_time_to_minutes_seconds(self, seconds: float) -> str:
        """秒数をm:ss.dd形式に変換

        Args:
            seconds: 変換する秒数

        Returns:
            m:ss.dd形式の時刻文字列（例: 81.23 -> 1:21.23）

        """
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:05.2f}"

    def _format_segments(self, segments: list[TranscriptionSegment]) -> str:
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
