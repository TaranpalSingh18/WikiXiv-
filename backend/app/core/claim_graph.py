from .schemas import ClaimRecord, ContradictionRecord, SourceRecord


NEGATIVE_MARKERS = ("not", "no", "fails", "limited", "insufficient", "unclear")


class ClaimGraphBuilder:
    def analyze(
        self,
        claims: list[ClaimRecord],
        sources: list[SourceRecord],
    ) -> tuple[list[ClaimRecord], list[ContradictionRecord]]:
        source_index = {row.id: row for row in sources}
        contradictions: list[ContradictionRecord] = []

        for claim in claims:
            claim.support_count = len(claim.evidence_ids)
            claim.conflict_count = 0

            conflict_ids: list[str] = []
            text = claim.statement.lower()
            has_negative = any(marker in text for marker in NEGATIVE_MARKERS)

            for evidence_id in claim.evidence_ids:
                source = source_index.get(evidence_id)
                if not source:
                    continue
                source_text = source.summary.lower()
                source_negative = any(marker in source_text for marker in NEGATIVE_MARKERS)
                if source_negative != has_negative:
                    claim.conflict_count += 1
                    conflict_ids.append(evidence_id)

            if claim.conflict_count > 0:
                claim.uncertainty_reason = "Evidence contains mixed positive and negative signals."
                contradictions.append(
                    ContradictionRecord(
                        claim_id=claim.id,
                        conflicting_source_ids=sorted(set(conflict_ids)),
                        note="Signals across sources do not fully agree.",
                    )
                )
            elif claim.support_count < 2:
                claim.uncertainty_reason = "Single-source evidence."
            else:
                claim.uncertainty_reason = ""

            claim.confidence = self._calibrate_confidence(claim)

        return claims, contradictions

    def _calibrate_confidence(self, claim: ClaimRecord) -> float:
        base = claim.confidence
        support_boost = min(0.18, 0.04 * max(claim.support_count - 1, 0))
        conflict_penalty = min(0.4, 0.12 * claim.conflict_count)
        adjusted = base + support_boost - conflict_penalty
        return max(0.1, min(0.99, adjusted))
