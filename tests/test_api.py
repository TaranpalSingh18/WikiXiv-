import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import main


class ApiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(main.app)

    def test_live_endpoint_contract(self) -> None:
        async def fake_research(question, max_results_per_source=4, mode="standard", progress_callback=None):
            event = {
                "stage": "source_discovery",
                "status": "done",
                "message": "ok",
                "timestamp_utc": "2026-01-01T00:00:00+00:00",
            }
            if progress_callback:
                progress_callback(event)
            return {
                "question": question,
                "mode": mode,
                "workflow": ["question_decomposed", "report_returned"],
                "executive_brief": "brief",
                "technical_report": "report",
                "claim_map": [],
                "contradictions": [],
                "confidence_table": [],
                "sources": [],
                "source_counts": {},
                "stage_events": [event],
                "errors": [],
                "integration_status": {"groq": True, "serpapi": True},
                "timestamp_utc": "2026-01-01T00:00:00+00:00",
            }

        with patch.object(main.assistant, "research", side_effect=fake_research):
            response = self.client.post(
                "/research/live",
                json={
                    "question": "What are latest efficient fine-tuning techniques?",
                    "max_results_per_source": 3,
                    "mode": "standard",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("report", payload)
        self.assertIn("events", payload)
        self.assertIsInstance(payload["events"], list)


if __name__ == "__main__":
    unittest.main()
