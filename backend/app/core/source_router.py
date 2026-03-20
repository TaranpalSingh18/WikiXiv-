import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

from .schemas import SourceRecord


USER_AGENT = "AIResearchAssistant/2.0 (+https://localhost)"


class SourceRouter:
    def __init__(self, serp_api_key: str) -> None:
        self.serp_api_key = serp_api_key.strip()

    def gather(self, query: str, limit: int) -> tuple[list[SourceRecord], list[str]]:
        sources: list[SourceRecord] = []
        errors: list[str] = []

        for name, fn in (
            ("Wikipedia", self._fetch_wikipedia),
            ("arXiv", self._fetch_arxiv),
            ("Web Search", self._fetch_web),
        ):
            try:
                results = fn(query, limit)
                sources.extend(results)
            except Exception as exc:
                errors.append(f"{name}: {exc}")

        return sources, errors

    def _fetch_wikipedia(self, query: str, limit: int) -> list[SourceRecord]:
        encoded = urllib.parse.quote(query)
        url = (
            "https://en.wikipedia.org/w/api.php"
            f"?action=query&list=search&srsearch={encoded}&format=json&srlimit={limit}"
        )
        payload = self._http_get_json(url)
        rows = payload.get("query", {}).get("search", [])

        records: list[SourceRecord] = []
        for idx, row in enumerate(rows[:limit], start=1):
            title = row.get("title", "Untitled")
            summary = self._strip_html(row.get("snippet", ""))
            page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
            records.append(
                SourceRecord(
                    id=f"wiki-{idx}",
                    source="Wikipedia",
                    title=title,
                    url=page_url,
                    summary=summary,
                    domain="wikipedia.org",
                )
            )
        return records

    def _fetch_arxiv(self, query: str, limit: int) -> list[SourceRecord]:
        encoded = urllib.parse.quote(query)
        url = (
            "http://export.arxiv.org/api/query"
            f"?search_query=all:{encoded}&start=0&max_results={limit}"
        )
        xml_text = self._http_get_text(url)
        root = ET.fromstring(xml_text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        records: list[SourceRecord] = []
        entries = root.findall("atom:entry", ns)
        for idx, entry in enumerate(entries[:limit], start=1):
            title = (entry.findtext("atom:title", default="Untitled", namespaces=ns) or "").strip()
            summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip()
            link = entry.findtext("atom:id", default="", namespaces=ns) or ""
            published = entry.findtext("atom:published", default="", namespaces=ns) or ""
            records.append(
                SourceRecord(
                    id=f"arxiv-{idx}",
                    source="arXiv",
                    title=" ".join(title.split()),
                    url=link,
                    summary=" ".join(summary.split()),
                    published_at=published,
                    domain="arxiv.org",
                )
            )
        return records

    def _fetch_web(self, query: str, limit: int) -> list[SourceRecord]:
        if self.serp_api_key:
            serp = self._fetch_serpapi(query, limit)
            if serp:
                return serp
        return self._fetch_duckduckgo(query, limit)

    def _fetch_serpapi(self, query: str, limit: int) -> list[SourceRecord]:
        encoded = urllib.parse.quote(query)
        key = urllib.parse.quote(self.serp_api_key)
        url = (
            "https://serpapi.com/search.json"
            f"?engine=google&q={encoded}&api_key={key}&num={limit}"
        )
        payload = self._http_get_json(url)
        rows = payload.get("organic_results", [])

        records: list[SourceRecord] = []
        for idx, row in enumerate(rows[:limit], start=1):
            link = row.get("link") or ""
            if not link:
                continue
            records.append(
                SourceRecord(
                    id=f"web-{idx}",
                    source="Web Search",
                    title=row.get("title") or "Untitled",
                    url=link,
                    summary=row.get("snippet") or "",
                    domain=self._extract_domain(link),
                )
            )
        return records

    def _fetch_duckduckgo(self, query: str, limit: int) -> list[SourceRecord]:
        encoded = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
        payload = self._http_get_json(url)

        rows: list[dict[str, Any]] = []
        related = payload.get("RelatedTopics", [])
        for row in related:
            if "Topics" in row:
                rows.extend(row.get("Topics", []))
            else:
                rows.append(row)

        records: list[SourceRecord] = []
        for idx, row in enumerate(rows, start=1):
            if len(records) >= limit:
                break
            text = row.get("Text")
            first_url = row.get("FirstURL")
            if not text or not first_url:
                continue
            records.append(
                SourceRecord(
                    id=f"web-{idx}",
                    source="Web Search",
                    title=text.split(" - ")[0],
                    url=first_url,
                    summary=text,
                    domain=self._extract_domain(first_url),
                )
            )
        return records

    def _http_get_json(self, url: str) -> dict[str, Any]:
        text = self._http_get_text(url)
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
        return {}

    def _http_get_text(self, url: str) -> str:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=25) as response:
            return response.read().decode("utf-8", errors="ignore")

    def _strip_html(self, value: str) -> str:
        return " ".join(
            value.replace('<span class="searchmatch">', "").replace("</span>", "").split()
        )

    def _extract_domain(self, link: str) -> str:
        parsed = urllib.parse.urlparse(link)
        return (parsed.netloc or "").lower()
