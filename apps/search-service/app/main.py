import os

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel

from packages.shared.internal_auth import decode_service_token
from packages.shared.ranking import score_candidate
from packages.shared.schemas import SearchResponse, SongCandidate
from packages.shared.security import validate_security_runtime

try:
    from yt_dlp import YoutubeDL
except Exception:
    YoutubeDL = None


app = FastAPI(title="search-service")
from packages.shared.observability import register_observability
register_observability(app, app.title)
validate_security_runtime()
SERVICE_NAME = os.getenv("SEARCH_SERVICE_NAME", "search-service")


class SearchRequest(BaseModel):
    query: str
    user_id: str | None = None


def fetch_youtube(query: str, limit: int = 20) -> list[dict]:
    if YoutubeDL is None:
        return []

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": True,
        "default_search": "ytsearch",
        "noplaylist": True,
        "ignoreerrors": True,
        "socket_timeout": 8,
    }
    last_error: Exception | None = None
    for _ in range(3):
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            return info.get("entries", []) if info else []
        except Exception as exc:
            last_error = exc
            continue
    if last_error:
        return []
    return []


def internal_service_dep(x_service_token: str | None = Header(default=None, alias="X-Service-Token")) -> dict:
    if not x_service_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing internal service token")
    try:
        return decode_service_token(x_service_token, SERVICE_NAME)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "search-service"}


@app.post("/internal/search", response_model=SearchResponse)
def search(payload: SearchRequest, _: dict = Depends(internal_service_dep)) -> SearchResponse:
    raw = fetch_youtube(payload.query, 20)
    if not raw:
        raw = [
            {"id": "demo-1", "title": f"{payload.query} Official Audio", "uploader": "Demo Artist", "duration": 210},
            {"id": "demo-2", "title": f"{payload.query} Topic", "uploader": "Demo Artist - Topic", "duration": 212},
            {"id": "demo-3", "title": f"{payload.query} Lyrics", "uploader": "Demo Lyrics", "duration": 208},
        ]

    ranked = []
    for item in raw:
        source_id = item.get("id")
        if not source_id:
            continue
        candidate = {
            "source_provider": "youtube",
            "source_id": source_id,
            "title": item.get("title") or "Unknown",
            "channel": item.get("channel") or item.get("uploader") or "Unknown",
            "duration_sec": item.get("duration"),
        }
        candidate["confidence_score"] = score_candidate(payload.query, candidate | item)
        ranked.append(candidate)

    ranked.sort(key=lambda x: x["confidence_score"], reverse=True)
    top = [SongCandidate(**c) for c in ranked[:3]]
    return SearchResponse(candidates=top, scoring_meta={"total_candidates": len(ranked), "version": "v1"})



