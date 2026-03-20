import unittest

from model.extractor import EvidenceExtractor
from model.ranker import SourceRanker
from model.schemas import SourceRecord


class PipelineUnitTests(unittest.TestCase):
    def test_ranker_scores_and_orders(self) -> None:
        ranker = SourceRanker()
        sources = [
            SourceRecord(
                id="s1",
                source="arXiv",
                title="Recent Transformer Scaling Results",
                url="https://arxiv.org/abs/1234.567",
                summary="Large models improve benchmark performance.",
                published_at="2026-01-01T00:00:00Z",
                domain="arxiv.org",
            ),
            SourceRecord(
                id="s2",
                source="Web Search",
                title="Blog opinion",
                url="https://example.com/blog",
                summary="Some thoughts about models.",
                domain="example.com",
            ),
        ]

        ranked = ranker.dedupe_and_rank("transformer benchmark performance", sources)
        self.assertEqual(len(ranked), 2)
        self.assertGreaterEqual(ranked[0].final_score, ranked[1].final_score)

    def test_extractor_generates_claims(self) -> None:
        extractor = EvidenceExtractor()
        sources = [
            SourceRecord(
                id="s1",
                source="arXiv",
                title="Paper",
                url="https://arxiv.org/abs/1",
                summary=(
                    "The method reduces hallucination in generation tasks by 22 percent. "
                    "Results are stable across three datasets."
                ),
                final_score=0.9,
            )
        ]

        claims = extractor.extract_claims(sources)
        self.assertGreaterEqual(len(claims), 1)
        self.assertTrue(claims[0].statement)
        self.assertGreater(claims[0].confidence, 0.2)


if __name__ == "__main__":
    unittest.main()
