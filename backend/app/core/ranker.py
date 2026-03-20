from datetime import datetime, timezone

from .schemas import SourceRecord


AUTHORITY_BOOSTS = {
    "wikipedia.org": 0.62,
    "arxiv.org": 0.86,
    "nature.com": 0.9,
    "science.org": 0.88,
    "nih.gov": 0.91,
    "who.int": 0.89,
    "openai.com": 0.75,
}


class SourceRanker:
    def dedupe_and_rank(self, query: str, sources: list[SourceRecord]) -> list[SourceRecord]:
        deduped = self._dedupe(sources)
        for row in deduped:
            row.trust_score = self._trust_score(row)
            row.freshness_score = self._freshness_score(row.published_at)
            row.relevance_score = self._relevance_score(query, row)
            row.final_score = (
                0.45 * row.trust_score
                + 0.25 * row.freshness_score
                + 0.30 * row.relevance_score
            )
            row.quality_reason = self._quality_reason(row)

        return sorted(deduped, key=lambda item: item.final_score, reverse=True)

    def _dedupe(self, sources: list[SourceRecord]) -> list[SourceRecord]:
        seen: set[str] = set()
        unique: list[SourceRecord] = []
        for row in sources:
            key = (row.url or row.title).strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            unique.append(row)
        return unique

    def _trust_score(self, row: SourceRecord) -> float:
        if row.domain in AUTHORITY_BOOSTS:
            return AUTHORITY_BOOSTS[row.domain]
        if row.source == "arXiv":
            return 0.8
        if row.source == "Wikipedia":
            return 0.65
        return 0.55

    def _freshness_score(self, published_at: str) -> float:
        if not published_at:
            return 0.55
        try:
            value = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            age_days = max((now - value).days, 0)
            if age_days <= 30:
                return 0.95
            if age_days <= 180:
                return 0.82
            if age_days <= 365:
                return 0.72
            if age_days <= 365 * 2:
                return 0.63
            return 0.48
        except Exception:
            return 0.55

    def _relevance_score(self, query: str, row: SourceRecord) -> float:
        query_tokens = {tok for tok in query.lower().split() if len(tok) > 2}
        content = f"{row.title} {row.summary}".lower()
        if not query_tokens:
            return 0.5
        overlap = sum(1 for token in query_tokens if token in content)
        return min(1.0, 0.35 + 0.12 * overlap)

    def _quality_reason(self, row: SourceRecord) -> str:
        reasons = []
        if row.trust_score >= 0.8:
            reasons.append("high-authority source")
        if row.freshness_score >= 0.8:
            reasons.append("recent evidence")
        if row.relevance_score >= 0.75:
            reasons.append("strong query match")
        if not reasons:
            reasons.append("baseline quality")
        return ", ".join(reasons)
