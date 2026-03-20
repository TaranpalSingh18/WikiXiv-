import json
import urllib.request
from datetime import datetime, timezone
from typing import Any

from .schemas import ClaimRecord, ContradictionRecord, ResearchOutput, SourceRecord


class ReportBuilder:
    def __init__(self, groq_api_key: str, groq_model: str) -> None:
        self.groq_api_key = groq_api_key.strip()
        self.groq_model = groq_model.strip() or "llama-3.1-8b-instant"

    def build(
        self,
        question: str,
        mode: str,
        workflow: list[str],
        sources: list[SourceRecord],
        claims: list[ClaimRecord],
        contradictions: list[ContradictionRecord],
        stage_events: list[dict[str, str]],
        errors: list[str],
        integration_status: dict[str, bool],
    ) -> dict[str, Any]:
        executive_brief = self._build_executive_brief(question, claims, contradictions)
        if self.groq_api_key:
            enriched = self._groq_brief(question, claims, contradictions)
            if enriched:
                executive_brief = enriched

        technical_report = self._build_technical_report(question, claims, contradictions, sources)

        output = ResearchOutput(
            question=question,
            mode=mode,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            workflow=workflow,
            executive_brief=executive_brief,
            technical_report=technical_report,
            claim_map=[
                {
                    "claim_id": claim.id,
                    "statement": claim.statement,
                    "confidence": round(claim.confidence, 3),
                    "evidence_ids": claim.evidence_ids,
                    "support_count": claim.support_count,
                    "conflict_count": claim.conflict_count,
                    "uncertainty_reason": claim.uncertainty_reason,
                }
                for claim in claims
            ],
            contradictions=[
                {
                    "claim_id": row.claim_id,
                    "conflicting_source_ids": row.conflicting_source_ids,
                    "note": row.note,
                }
                for row in contradictions
            ],
            confidence_table=[
                {
                    "claim_id": claim.id,
                    "confidence": round(claim.confidence, 3),
                    "grade": self._grade(claim.confidence),
                    "support_count": claim.support_count,
                    "conflict_count": claim.conflict_count,
                }
                for claim in claims
            ],
            sources=[
                {
                    "id": row.id,
                    "source": row.source,
                    "title": row.title,
                    "url": row.url,
                    "summary": row.summary,
                    "published_at": row.published_at,
                    "domain": row.domain,
                    "scores": {
                        "trust": round(row.trust_score, 3),
                        "freshness": round(row.freshness_score, 3),
                        "relevance": round(row.relevance_score, 3),
                        "final": round(row.final_score, 3),
                    },
                    "quality_reason": row.quality_reason,
                }
                for row in sources
            ],
            source_counts=self._source_counts(sources),
            stage_events=stage_events,
            errors=errors,
            integration_status=integration_status,
        )
        return output.to_dict()

    def _build_executive_brief(
        self,
        question: str,
        claims: list[ClaimRecord],
        contradictions: list[ContradictionRecord],
    ) -> str:
        top_claims = sorted(claims, key=lambda row: row.confidence, reverse=True)[:4]
        lines = [f"Question: {question}", "Top findings:"]
        for row in top_claims:
            lines.append(f"- ({row.id}) {row.statement} [confidence={row.confidence:.2f}]")
        if contradictions:
            lines.append(f"Conflicts detected: {len(contradictions)} claim(s) require careful interpretation.")
        else:
            lines.append("No significant contradictions detected across the top evidence.")
        return "\n".join(lines)

    def _build_technical_report(
        self,
        question: str,
        claims: list[ClaimRecord],
        contradictions: list[ContradictionRecord],
        sources: list[SourceRecord],
    ) -> str:
        sections = []
        sections.append(f"# Research Question\n{question}")
        sections.append("# Method\nMulti-source retrieval, authority-aware ranking, claim extraction, and contradiction analysis.")

        key_findings = sorted(claims, key=lambda row: row.confidence, reverse=True)[:8]
        findings_lines = []
        for row in key_findings:
            citations = ", ".join(row.evidence_ids)
            findings_lines.append(f"- {row.statement} (confidence={row.confidence:.2f}; evidence={citations})")
        sections.append("# Key Findings\n" + ("\n".join(findings_lines) if findings_lines else "No findings generated."))

        if contradictions:
            conflict_lines = [
                f"- {row.claim_id}: {row.note} (sources={', '.join(row.conflicting_source_ids)})"
                for row in contradictions
            ]
            sections.append("# Conflicting Evidence\n" + "\n".join(conflict_lines))
        else:
            sections.append("# Conflicting Evidence\nNo major conflicts detected.")

        sections.append(
            "# Limitations\n"
            "- Retrieval is bounded by API limits and query phrasing.\n"
            "- Some evidence comes from summaries instead of full-text documents.\n"
            "- Confidence is calibrated heuristically and should not be treated as ground truth."
        )

        citation_lines = [f"- [{row.id}] {row.title} ({row.url})" for row in sources[:20]]
        sections.append("# Citations\n" + "\n".join(citation_lines))

        sections.append(
            "# Next Actions\n"
            "- Validate top claims against full papers and primary datasets.\n"
            "- Add domain-specific experts for deeper evidence extraction.\n"
            "- Re-run in deep mode with expanded result limits."
        )

        return "\n\n".join(sections)

    def _groq_brief(
        self,
        question: str,
        claims: list[ClaimRecord],
        contradictions: list[ContradictionRecord],
    ) -> str:
        top_claims = sorted(claims, key=lambda row: row.confidence, reverse=True)[:7]
        evidence = []
        for row in top_claims:
            evidence.append(
                f"- {row.statement} [claim={row.id}; confidence={row.confidence:.2f}; evidence={','.join(row.evidence_ids)}]"
            )

        prompt = (
            "Create an executive brief with: overview, 3-5 bullet findings, risk notes, and confidence caveat. "
            "Use only provided evidence and be explicit when uncertainty exists.\n\n"
            f"Question: {question}\n"
            f"Contradictions: {len(contradictions)}\n"
            "Evidence:\n"
            + "\n".join(evidence)
        )

        payload = {
            "model": self.groq_model,
            "messages": [
                {"role": "system", "content": "You are a rigorous research analyst."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 550,
        }

        try:
            request = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "User-Agent": "AIResearchAssistant/2.0",
                },
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=35) as response:
                text = response.read().decode("utf-8", errors="ignore")
            parsed = json.loads(text)
            content = (
                parsed.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            return content
        except Exception:
            return ""

    def _source_counts(self, sources: list[SourceRecord]) -> dict[str, int]:
        result: dict[str, int] = {}
        for row in sources:
            result[row.source] = result.get(row.source, 0) + 1
        return result

    def _grade(self, confidence: float) -> str:
        if confidence >= 0.85:
            return "high"
        if confidence >= 0.65:
            return "medium"
        return "low"
