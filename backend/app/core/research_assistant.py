import asyncio
import os
from collections.abc import Callable
from typing import Any

from .claim_graph import ClaimGraphBuilder
from .extractor import EvidenceExtractor
from .ranker import SourceRanker
from .report_builder import ReportBuilder
from .schemas import PipelineEvent
from .source_router import SourceRouter


ProgressCallback = Callable[[dict[str, str]], None]


class ResearchAssistant:
    def __init__(self) -> None:
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
        self.serp_api_key = (
            os.getenv("SERPAPI_API_KEY", "").strip() or os.getenv("SERP_API_KEY", "").strip()
        )

        self.router = SourceRouter(serp_api_key=self.serp_api_key)
        self.ranker = SourceRanker()
        self.extractor = EvidenceExtractor()
        self.graph = ClaimGraphBuilder()
        self.builder = ReportBuilder(
            groq_api_key=self.groq_api_key,
            groq_model=self.groq_model,
        )

    async def research(
        self,
        question: str,
        max_results_per_source: int = 4,
        mode: str = "standard",
        progress_callback: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        query = (question or "").strip()
        if len(query) < 5:
            raise ValueError("Question must be at least 5 characters long.")

        mode_value = (mode or "standard").strip().lower()
        if mode_value not in {"fast", "standard", "deep"}:
            raise ValueError("mode must be one of: fast, standard, deep")

        depth = self._depth_limit(mode_value, max_results_per_source)
        events: list[dict[str, str]] = []
        errors: list[str] = []
        workflow: list[str] = []

        def emit(stage: str, status: str, message: str) -> None:
            event = PipelineEvent(stage=stage, status=status, message=message)
            event_dict = {
                "stage": event.stage,
                "status": event.status,
                "message": event.message,
                "timestamp_utc": event.timestamp_utc,
            }
            events.append(event_dict)
            if progress_callback:
                progress_callback(event_dict)

        emit("question_decomposition", "running", "Breaking the question into retrieval intent.")
        retrieval_query = self._decompose_question(query)
        workflow.append("question_decomposed")
        emit("question_decomposition", "done", f"Decomposed query: {retrieval_query}")

        emit("source_discovery", "running", "Collecting results from Wikipedia, arXiv, and web.")
        sources, discovery_errors = await asyncio.to_thread(self.router.gather, retrieval_query, depth)
        errors.extend(discovery_errors)
        workflow.append("sources_discovered")
        emit("source_discovery", "done", f"Collected {len(sources)} raw sources.")

        emit("source_quality_scoring", "running", "Ranking sources by authority, freshness, and relevance.")
        ranked_sources = await asyncio.to_thread(self.ranker.dedupe_and_rank, query, sources)
        workflow.append("sources_ranked")
        emit("source_quality_scoring", "done", f"Ranked {len(ranked_sources)} unique sources.")

        emit("evidence_extraction", "running", "Extracting atomic claims from top sources.")
        claim_limit = self._claim_limit(mode_value)
        claims = await asyncio.to_thread(self.extractor.extract_claims, ranked_sources[: depth * 2])
        claims = claims[:claim_limit]
        workflow.append("claims_extracted")
        emit("evidence_extraction", "done", f"Extracted {len(claims)} candidate claims.")

        emit("claim_graph_analysis", "running", "Checking support and contradictions across evidence.")
        claims, contradictions = await asyncio.to_thread(self.graph.analyze, claims, ranked_sources)
        workflow.append("claim_graph_built")
        emit(
            "claim_graph_analysis",
            "done",
            f"Found {len(contradictions)} contradictory claim clusters.",
        )

        emit("report_synthesis", "running", "Drafting executive brief and technical report.")
        report = await asyncio.to_thread(
            self.builder.build,
            question,
            mode_value,
            workflow,
            ranked_sources[: depth * 3],
            claims,
            contradictions,
            events,
            errors,
            {
                "groq": bool(self.groq_api_key),
                "serpapi": bool(self.serp_api_key),
            },
        )
        workflow.append("report_returned")
        emit("report_synthesis", "done", "Structured report generated successfully.")

        report["workflow"] = workflow
        report["stage_events"] = events
        return report

    def _decompose_question(self, question: str) -> str:
        simplified = " ".join(question.split())
        if "?" in simplified:
            simplified = simplified.replace("?", "")
        return simplified

    def _depth_limit(self, mode: str, requested_limit: int) -> int:
        if mode == "fast":
            return min(3, max(2, requested_limit))
        if mode == "deep":
            return min(10, max(5, requested_limit + 2))
        return min(7, max(3, requested_limit))

    def _claim_limit(self, mode: str) -> int:
        if mode == "fast":
            return 8
        if mode == "deep":
            return 20
        return 12
