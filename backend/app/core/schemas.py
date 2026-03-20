from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class SourceRecord:
    id: str
    source: str
    title: str
    url: str
    summary: str
    published_at: str = ""
    domain: str = ""
    trust_score: float = 0.0
    freshness_score: float = 0.0
    relevance_score: float = 0.0
    final_score: float = 0.0
    quality_reason: str = ""


@dataclass
class ClaimRecord:
    id: str
    statement: str
    confidence: float
    evidence_ids: list[str] = field(default_factory=list)
    support_count: int = 0
    conflict_count: int = 0
    uncertainty_reason: str = ""


@dataclass
class ContradictionRecord:
    claim_id: str
    conflicting_source_ids: list[str]
    note: str


@dataclass
class PipelineEvent:
    stage: str
    status: str
    message: str
    timestamp_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class ResearchOutput:
    question: str
    mode: str
    timestamp_utc: str
    workflow: list[str]
    executive_brief: str
    technical_report: str
    claim_map: list[dict[str, Any]]
    contradictions: list[dict[str, Any]]
    confidence_table: list[dict[str, Any]]
    sources: list[dict[str, Any]]
    source_counts: dict[str, int]
    stage_events: list[dict[str, str]]
    errors: list[str]
    integration_status: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
