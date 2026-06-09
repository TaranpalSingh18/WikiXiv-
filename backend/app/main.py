from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from core.research_assistant import ResearchAssistant


load_dotenv()

app = FastAPI(title="AI Research Assistant", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
assistant = ResearchAssistant()


class ResearchRequest(BaseModel):
    question: str = Field(min_length=5, max_length=500)
    max_results_per_source: int = Field(default=4, ge=1, le=10)
    mode: str = Field(default="standard")


class LiveResearchResponse(BaseModel):
    report: dict
    events: list[dict]


@app.get("/")
async def get_health():
    return {"message": "ok health", "service": "ai-research-assistant"}


@app.post("/research")
async def run_research(request: ResearchRequest):
    try:
        report = await assistant.research(
            question=request.question,
            max_results_per_source=request.max_results_per_source,
            mode=request.mode,
        )
        return report
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Research failed: {exc}") from exc


@app.post("/research/live", response_model=LiveResearchResponse)
async def run_research_live(request: ResearchRequest):
    try:
        events: list[dict] = []

        def _progress(event: dict[str, str]) -> None:
            events.append(event)

        report = await assistant.research(
            question=request.question,
            max_results_per_source=request.max_results_per_source,
            mode=request.mode,
            progress_callback=_progress,
        )
        return LiveResearchResponse(report=report, events=events)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Live research failed: {exc}") from exc

