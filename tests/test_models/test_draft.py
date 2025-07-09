"""draft.pyのテスト"""

from src.models.transcription import TranscriptionSegment, TranscriptionResult
from src.models.draft import ShortVideoProposal, DraftResult


class TestShortVideoProposal:
    """ShortVideoProposalのテストクラス"""

    def test_instance_creation(self):
        """インスタンス生成のテスト"""
        proposal = ShortVideoProposal(
            title="面白いトーク集",
            start_time=30.0,
            end_time=90.0,
            caption="今日の面白い話をまとめました！",
            key_points=["ポイント1", "ポイント2"],
        )

        assert proposal.title == "面白いトーク集"
        assert proposal.start_time == 30.0
        assert proposal.end_time == 90.0
        assert proposal.caption == "今日の面白い話をまとめました！"
        assert proposal.key_points == ["ポイント1", "ポイント2"]

    def test_equality_comparison(self):
        """等価性比較のテスト"""
        proposal1 = ShortVideoProposal(
            title="テスト",
            start_time=0.0,
            end_time=10.0,
            caption="テストキャプション",
            key_points=["ポイント1"],
        )
        proposal2 = ShortVideoProposal(
            title="テスト",
            start_time=0.0,
            end_time=10.0,
            caption="テストキャプション",
            key_points=["ポイント1"],
        )
        proposal3 = ShortVideoProposal(
            title="別のテスト",
            start_time=0.0,
            end_time=10.0,
            caption="テストキャプション",
            key_points=["ポイント1"],
        )

        assert proposal1 == proposal2
        assert proposal1 != proposal3

    def test_string_representation(self):
        """文字列表現のテスト"""
        proposal = ShortVideoProposal(
            title="テスト動画",
            start_time=0.0,
            end_time=30.0,
            caption="テストキャプション",
            key_points=["ポイント1"],
        )
        str_repr = str(proposal)

        assert "ShortVideoProposal" in str_repr
        assert "テスト動画" in str_repr

    def test_time_consistency(self):
        """時刻の論理的整合性のテスト"""
        # 正常なケース
        proposal = ShortVideoProposal(
            title="テスト", start_time=10.0, end_time=60.0, caption="テスト", key_points=[]
        )
        assert proposal.start_time < proposal.end_time

        # 同じ時刻のケース（瞬間的なクリップ）
        instant_proposal = ShortVideoProposal(
            title="瞬間", start_time=5.0, end_time=5.0, caption="瞬間的なクリップ", key_points=[]
        )
        assert instant_proposal.start_time == instant_proposal.end_time

    def test_field_types(self):
        """フィールドの型の正確性のテスト"""
        proposal = ShortVideoProposal(
            title="テスト",
            start_time=0.0,
            end_time=30.0,
            caption="テスト",
            key_points=["ポイント1", "ポイント2"],
        )

        assert isinstance(proposal.title, str)
        assert isinstance(proposal.start_time, float)
        assert isinstance(proposal.end_time, float)
        assert isinstance(proposal.caption, str)
        assert isinstance(proposal.key_points, list)
        assert all(isinstance(point, str) for point in proposal.key_points)

    def test_empty_key_points(self):
        """空のキーポイントリストのテスト"""
        proposal = ShortVideoProposal(
            title="テスト", start_time=0.0, end_time=30.0, caption="テスト", key_points=[]
        )

        assert len(proposal.key_points) == 0
        assert proposal.key_points == []


class TestDraftResult:
    """DraftResultのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行される準備処理"""
        self.sample_segments = [TranscriptionSegment(0.0, 10.0, "テスト文字起こし")]
        self.sample_transcription = TranscriptionResult(
            segments=self.sample_segments, full_text="テスト文字起こし"
        )
        self.sample_proposals = [
            ShortVideoProposal(
                title="タイトル1",
                start_time=0.0,
                end_time=5.0,
                caption="キャプション1",
                key_points=["ポイント1"],
            )
        ]

    def test_instance_creation(self):
        """インスタンス生成のテスト"""
        draft = DraftResult(
            proposals=self.sample_proposals,
            original_transcription=self.sample_transcription,
        )

        assert len(draft.proposals) == 1
        assert draft.original_transcription == self.sample_transcription

    def test_equality_comparison(self):
        """等価性比較のテスト"""
        draft1 = DraftResult(
            proposals=self.sample_proposals,
            original_transcription=self.sample_transcription,
        )
        draft2 = DraftResult(
            proposals=self.sample_proposals,
            original_transcription=self.sample_transcription,
        )

        different_proposals = [
            ShortVideoProposal(
                title="別のタイトル",
                start_time=0.0,
                end_time=5.0,
                caption="別のキャプション",
                key_points=["別のポイント"],
            )
        ]
        draft3 = DraftResult(
            proposals=different_proposals,
            original_transcription=self.sample_transcription,
        )

        assert draft1 == draft2
        assert draft1 != draft3

    def test_string_representation(self):
        """文字列表現のテスト"""
        draft = DraftResult(
            proposals=self.sample_proposals,
            original_transcription=self.sample_transcription,
        )
        str_repr = str(draft)

        assert "DraftResult" in str_repr

    def test_multiple_proposals(self):
        """複数の企画提案のテスト"""
        multiple_proposals = [
            ShortVideoProposal(
                title="提案1",
                start_time=0.0,
                end_time=30.0,
                caption="キャプション1",
                key_points=["ポイント1-1", "ポイント1-2"],
            ),
            ShortVideoProposal(
                title="提案2",
                start_time=30.0,
                end_time=60.0,
                caption="キャプション2",
                key_points=["ポイント2-1"],
            ),
            ShortVideoProposal(
                title="提案3",
                start_time=60.0,
                end_time=90.0,
                caption="キャプション3",
                key_points=[],
            ),
        ]

        draft = DraftResult(
            proposals=multiple_proposals,
            original_transcription=self.sample_transcription,
        )

        assert len(draft.proposals) == 3
        assert draft.proposals[0].title == "提案1"
        assert draft.proposals[1].title == "提案2"
        assert draft.proposals[2].title == "提案3"

    def test_empty_proposals(self):
        """空の企画提案リストのテスト"""
        draft = DraftResult(
            proposals=[], original_transcription=self.sample_transcription
        )

        assert len(draft.proposals) == 0
        assert draft.proposals == []

    def test_field_types(self):
        """フィールドの型の正確性のテスト"""
        draft = DraftResult(
            proposals=self.sample_proposals,
            original_transcription=self.sample_transcription,
        )

        assert isinstance(draft.proposals, list)
        assert isinstance(draft.original_transcription, TranscriptionResult)
        assert all(
            isinstance(proposal, ShortVideoProposal) for proposal in draft.proposals
        )


class TestSampleData:
    """サンプルデータを使った統合テスト"""

    def test_sample_draft_data(self):
        """設計書のサンプルデータでのテスト"""
        # サンプル文字起こしデータ
        segments = [TranscriptionSegment(0.0, 10.0, "テスト文字起こし")]
        transcription = TranscriptionResult(segments, "テスト文字起こし")

        # サンプル企画提案データ
        proposals = [
            ShortVideoProposal(
                title="タイトル1",
                start_time=0.0,
                end_time=5.0,
                caption="キャプション1",
                key_points=["ポイント1"],
            )
        ]

        draft = DraftResult(proposals, transcription)

        # 基本的な検証
        assert len(draft.proposals) == 1
        assert draft.original_transcription == transcription

        # 企画提案の内容検証
        proposal = draft.proposals[0]
        assert proposal.title == "タイトル1"
        assert proposal.start_time == 0.0
        assert proposal.end_time == 5.0
        assert proposal.caption == "キャプション1"
        assert proposal.key_points == ["ポイント1"]

    def test_realistic_usage_pattern(self):
        """実際の使用パターンに近いテスト"""
        # より現実的な文字起こしデータ
        segments = [
            TranscriptionSegment(0.0, 15.0, "今日はPythonの基本について説明します"),
            TranscriptionSegment(15.0, 30.0, "まずは変数の定義から始めましょう"),
            TranscriptionSegment(30.0, 45.0, "次に関数の作り方を見ていきます"),
            TranscriptionSegment(45.0, 60.0, "最後にクラスについて説明します"),
        ]

        full_text = (
            "今日はPythonの基本について説明しますまずは変数の定義から始めましょう次に関数の作り方を見ていきます最後にクラスについて説明します"
        )
        transcription = TranscriptionResult(segments, full_text)

        # 複数の企画提案
        proposals = [
            ShortVideoProposal(
                title="Python基本講座 - 変数編",
                start_time=0.0,
                end_time=30.0,
                caption="Pythonの変数について分かりやすく解説！ #Python #プログラミング初心者",
                key_points=["変数の基本概念", "変数の定義方法", "実際のコード例"],
            ),
            ShortVideoProposal(
                title="Python基本講座 - 関数編",
                start_time=15.0,
                end_time=45.0,
                caption="関数の作り方をマスターしよう！ #Python #関数",
                key_points=["関数の定義", "引数と戻り値", "実践的な使い方"],
            ),
            ShortVideoProposal(
                title="Python基本講座 - クラス編",
                start_time=30.0,
                end_time=60.0,
                caption="オブジェクト指向プログラミングの基礎 #Python #OOP",
                key_points=["クラスの概念", "インスタンスの作成", "メソッドの定義"],
            ),
        ]

        draft = DraftResult(proposals, transcription)

        # 全体の検証
        assert len(draft.proposals) == 3
        assert len(draft.original_transcription.segments) == 4

        # 各提案の時間範囲が元の文字起こし範囲内にあることを確認
        total_duration = transcription.segments[-1].end_time
        for proposal in draft.proposals:
            assert 0.0 <= proposal.start_time <= total_duration
            assert 0.0 <= proposal.end_time <= total_duration
            assert proposal.start_time <= proposal.end_time

        # キーポイントの内容確認
        assert len(draft.proposals[0].key_points) == 3
        assert len(draft.proposals[1].key_points) == 3
        assert len(draft.proposals[2].key_points) == 3
