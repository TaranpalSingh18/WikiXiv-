import re

from .schemas import ClaimRecord, SourceRecord


class EvidenceExtractor:
    def extract_claims(self, sources: list[SourceRecord]) -> list[ClaimRecord]:
        claims: list[ClaimRecord] = []
        next_id = 1

        for source in sources:
            sentences = self._split_sentences(source.summary)
            for sentence in sentences[:2]:
                normalized = sentence.strip()
                if len(normalized) < 35:
                    continue
                confidence = self._sentence_confidence(normalized, source.final_score)
                claims.append(
                    ClaimRecord(
                        id=f"claim-{next_id}",
                        statement=normalized,
                        confidence=confidence,
                        evidence_ids=[source.id],
                    )
                )
                next_id += 1

        return self._merge_similar_claims(claims)

    def _split_sentences(self, text: str) -> list[str]:
        if not text:
            return []
        chunks = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
        return [chunk for chunk in chunks if chunk]

    def _sentence_confidence(self, sentence: str, source_score: float) -> float:
        hedges = ("may", "might", "could", "possible", "preliminary")
        penalty = 0.08 if any(h in sentence.lower() for h in hedges) else 0.0
        return max(0.25, min(0.98, source_score - penalty))

    def _merge_similar_claims(self, claims: list[ClaimRecord]) -> list[ClaimRecord]:
        merged: list[ClaimRecord] = []
        for claim in claims:
            key = self._claim_key(claim.statement)
            match = next((row for row in merged if self._claim_key(row.statement) == key), None)
            if not match:
                merged.append(claim)
                continue
            match.evidence_ids.extend(claim.evidence_ids)
            match.evidence_ids = sorted(set(match.evidence_ids))
            match.confidence = max(match.confidence, claim.confidence)
        return merged

    def _claim_key(self, statement: str) -> str:
        words = [w for w in re.findall(r"[a-z0-9]+", statement.lower()) if len(w) > 3]
        return " ".join(words[:10])
