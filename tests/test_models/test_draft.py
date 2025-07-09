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
            first_impact="面白い話があります",
            last_conclusion="とても勉強になりました",
            summary="今日の面白いトークをまとめた動画",
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
            first_impact="テストインパクト",
            last_conclusion="テスト結論",
            summary="テスト概要",
        )
        proposal2 = ShortVideoProposal(
            title="テスト",
            start_time=0.0,
            end_time=10.0,
            caption="テストキャプション",
            key_points=["ポイント1"],
            first_impact="テストインパクト",
            last_conclusion="テスト結論",
            summary="テスト概要",
        )
        proposal3 = ShortVideoProposal(
            title="別のテスト",
            start_time=0.0,
            end_time=10.0,
            caption="テストキャプション",
            key_points=["ポイント1"],
            first_impact="別のインパクト",
            last_conclusion="別の結論",
            summary="別の概要",
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
            first_impact="テストインパクト",
            last_conclusion="テスト結論",
            summary="テスト概要",
        )
        str_repr = str(proposal)

        assert "ShortVideoProposal" in str_repr
        assert "テスト動画" in str_repr

    def test_time_consistency(self):
        """時刻の論理的整合性のテスト"""
        # 正常なケース
        proposal = ShortVideoProposal(
            title="テスト",
            start_time=10.0,
            end_time=60.0,
            caption="テスト",
            key_points=[],
            first_impact="テストインパクト",
            last_conclusion="テスト結論",
            summary="テスト概要",
        )
        assert proposal.start_time < proposal.end_time

        # 同じ時刻のケース（瞬間的なクリップ）
        instant_proposal = ShortVideoProposal(
            title="瞬間",
            start_time=5.0,
            end_time=5.0,
            caption="瞬間的なクリップ",
            key_points=[],
            first_impact="瞬間インパクト",
            last_conclusion="瞬間結論",
            summary="瞬間概要",
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
            first_impact="テストインパクト",
            last_conclusion="テスト結論",
            summary="テスト概要",
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
            title="テスト",
            start_time=0.0,
            end_time=30.0,
            caption="テスト",
            key_points=[],
            first_impact="テストインパクト",
            last_conclusion="テスト結論",
            summary="テスト概要",
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
                first_impact="インパクト1",
                last_conclusion="結論1",
                summary="概要1",
            )
        ]

    def test_instance_creation(self):
        """インスタンス生成のテスト"""
        draft = DraftResult(
            proposals=self.sample_proposals,
            total_count=len(self.sample_proposals),
        )

        assert len(draft.proposals) == 1
        assert draft.total_count == len(self.sample_proposals)

    def test_equality_comparison(self):
        """等価性比較のテスト"""
        draft1 = DraftResult(
            proposals=self.sample_proposals,
            total_count=len(self.sample_proposals),
        )
        draft2 = DraftResult(
            proposals=self.sample_proposals,
            total_count=len(self.sample_proposals),
        )

        different_proposals = [
            ShortVideoProposal(
                title="別のタイトル",
                start_time=0.0,
                end_time=5.0,
                caption="別のキャプション",
                key_points=["別のポイント"],
                first_impact="別のインパクト",
                last_conclusion="別の結論",
                summary="別の概要",
            )
        ]
        draft3 = DraftResult(
            proposals=different_proposals,
            total_count=len(different_proposals),
        )

        assert draft1 == draft2
        assert draft1 != draft3

    def test_string_representation(self):
        """文字列表現のテスト"""
        draft = DraftResult(
            proposals=self.sample_proposals,
            total_count=len(self.sample_proposals),
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
                first_impact="インパクト1",
                last_conclusion="結論1",
                summary="概要1",
            ),
            ShortVideoProposal(
                title="提案2",
                start_time=30.0,
                end_time=60.0,
                caption="キャプション2",
                key_points=["ポイント2-1"],
                first_impact="インパクト2",
                last_conclusion="結論2",
                summary="概要2",
            ),
            ShortVideoProposal(
                title="提案3",
                start_time=60.0,
                end_time=90.0,
                caption="キャプション3",
                key_points=[],
                first_impact="インパクト3",
                last_conclusion="結論3",
                summary="概要3",
            ),
        ]

        draft = DraftResult(
            proposals=multiple_proposals,
            total_count=len(multiple_proposals),
        )

        assert len(draft.proposals) == 3
        assert draft.proposals[0].title == "提案1"
        assert draft.proposals[1].title == "提案2"
        assert draft.proposals[2].title == "提案3"

    def test_empty_proposals(self):
        """空の企画提案リストのテスト"""
        draft = DraftResult(proposals=[], total_count=0)

        assert len(draft.proposals) == 0
        assert draft.proposals == []

    def test_field_types(self):
        """フィールドの型の正確性のテスト"""
        draft = DraftResult(
            proposals=self.sample_proposals,
            total_count=len(self.sample_proposals),
        )

        assert isinstance(draft.proposals, list)
        assert isinstance(draft.total_count, int)
        assert all(
            isinstance(proposal, ShortVideoProposal) for proposal in draft.proposals
        )


class TestSampleData:
    """サンプルデータを使った統合テスト"""

    def test_sample_draft_data(self):
        """設計書のサンプルデータでのテスト"""
        # サンプル文字起こしデータ

        # サンプル企画提案データ
        proposals = [
            ShortVideoProposal(
                title="タイトル1",
                start_time=0.0,
                end_time=5.0,
                caption="キャプション1",
                key_points=["ポイント1"],
                first_impact="インパクト1",
                last_conclusion="結論1",
                summary="概要1",
            )
        ]

        draft = DraftResult(proposals, len(proposals))

        # 基本的な検証
        assert len(draft.proposals) == 1
        assert draft.total_count == len(proposals)

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

        full_text = "今日はPythonの基本について説明しますまずは変数の定義から始めましょう次に関数の作り方を見ていきます最後にクラスについて説明します"
        transcription = TranscriptionResult(segments, full_text)

        # 複数の企画提案
        proposals = [
            ShortVideoProposal(
                title="Python基本講座 - 変数編",
                start_time=0.0,
                end_time=30.0,
                caption="Pythonの変数について分かりやすく解説！ #Python #プログラミング初心者",
                key_points=["変数の基本概念", "変数の定義方法", "実際のコード例"],
                first_impact="今日はPythonの基本について",
                last_conclusion="変数をマスターしましょう",
                summary="Pythonの変数の基本を学ぶ",
            ),
            ShortVideoProposal(
                title="Python基本講座 - 関数編",
                start_time=15.0,
                end_time=45.0,
                caption="関数の作り方をマスターしよう！ #Python #関数",
                key_points=["関数の定義", "引数と戻り値", "実践的な使い方"],
                first_impact="次に関数の作り方を",
                last_conclusion="関数を使いこなそう",
                summary="Pythonの関数の作り方を学ぶ",
            ),
            ShortVideoProposal(
                title="Python基本講座 - クラス編",
                start_time=30.0,
                end_time=60.0,
                caption="オブジェクト指向プログラミングの基礎 #Python #OOP",
                key_points=["クラスの概念", "インスタンスの作成", "メソッドの定義"],
                first_impact="最後にクラスについて",
                last_conclusion="オブジェクト指向をマスター",
                summary="Pythonのクラスの基本を学ぶ",
            ),
        ]

        draft = DraftResult(proposals, len(proposals))

        # 全体の検証
        assert len(draft.proposals) == 3
        assert draft.total_count == 3

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
