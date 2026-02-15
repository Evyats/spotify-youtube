import os

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from packages.shared.schemas import ImportSongRequest, RefreshRequest, SignInRequest, SignUpRequest, VerifyEmailRequest
from packages.shared.security import decode_token


app = FastAPI(title="api-gateway")
from packages.shared.observability import register_observability
register_observability(app, app.title)

allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
SEARCH_SERVICE_URL = os.getenv("SEARCH_SERVICE_URL", "http://search-service:8000")
DOWNLOAD_SERVICE_URL = os.getenv("DOWNLOAD_SERVICE_URL", "http://download-service:8000")
CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://catalog-service:8000")
STREAM_SERVICE_URL = os.getenv("STREAM_SERVICE_URL", "http://stream-service:8000")
ADMIN_SERVICE_URL = os.getenv("ADMIN_SERVICE_URL", "http://admin-service:8000")


def bearer_token_dep(authorization: str | None = Header(default=None, alias="Authorization")) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        claims = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    if claims.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token type")
    return claims


def require_admin(claims: dict = Depends(bearer_token_dep)) -> dict:
    if claims.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin required")
    return claims


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api-gateway"}


@app.post("/auth/signup")
async def signup(payload: SignUpRequest):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{AUTH_SERVICE_URL}/internal/signup", json=payload.model_dump())
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


@app.post("/auth/verify-email")
async def verify_email(payload: VerifyEmailRequest):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{AUTH_SERVICE_URL}/internal/verify-email", json=payload.model_dump())
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


@app.post("/auth/signin")
async def signin(payload: SignInRequest):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{AUTH_SERVICE_URL}/internal/signin", json=payload.model_dump())
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


@app.post("/auth/refresh")
async def refresh(payload: RefreshRequest):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{AUTH_SERVICE_URL}/internal/refresh", json=payload.model_dump())
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


@app.get("/auth/google/login")
async def google_login():
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{AUTH_SERVICE_URL}/internal/oauth/google/login")
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


@app.get("/auth/google/callback")
async def google_callback(code: str):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{AUTH_SERVICE_URL}/internal/oauth/google/callback", params={"code": code})
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


@app.get("/songs/search")
async def search(q: str, claims: dict = Depends(bearer_token_dep)):
    req = {"query": q, "user_id": claims.get("sub")}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{SEARCH_SERVICE_URL}/internal/search", json=req)
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


@app.post("/songs/import")
async def import_song(payload: ImportSongRequest, claims: dict = Depends(bearer_token_dep)):
    req = {
        "user_id": claims.get("sub"),
        "source_provider": payload.source_provider,
        "source_video_id": payload.source_id,
        "title": payload.title,
        "artist": payload.artist,
        "candidate_meta": payload.candidate_meta,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{DOWNLOAD_SERVICE_URL}/internal/jobs", json=req)
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


@app.get("/library")
async def library(claims: dict = Depends(bearer_token_dep)):
    user_id = claims.get("sub")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{CATALOG_SERVICE_URL}/internal/library/{user_id}")
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


@app.get("/stream/{song_id}")
async def stream(song_id: str, claims: dict = Depends(bearer_token_dep)):
    user_id = claims.get("sub")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{STREAM_SERVICE_URL}/internal/stream-url/{song_id}", params={"user_id": user_id})
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    stream_url = r.json().get("stream_url")
    if not stream_url:
        raise HTTPException(status_code=500, detail="missing stream url")
    return {"stream_url": stream_url}


@app.get("/jobs/{job_id}")
async def job_status(job_id: str, claims: dict = Depends(bearer_token_dep)):
    user_id = claims.get("sub")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{DOWNLOAD_SERVICE_URL}/internal/jobs/{job_id}", params={"user_id": user_id})
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


@app.get("/admin/users")
async def admin_users(_: dict = Depends(require_admin), authorization: str | None = Header(default=None, alias="Authorization")):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{ADMIN_SERVICE_URL}/internal/admin/users",
            headers={"Authorization": authorization or ""},
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


@app.get("/admin/songs")
async def admin_songs(_: dict = Depends(require_admin), authorization: str | None = Header(default=None, alias="Authorization")):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{ADMIN_SERVICE_URL}/internal/admin/songs",
            headers={"Authorization": authorization or ""},
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


@app.get("/admin/jobs")
async def admin_jobs(_: dict = Depends(require_admin), authorization: str | None = Header(default=None, alias="Authorization")):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{ADMIN_SERVICE_URL}/internal/admin/jobs",
            headers={"Authorization": authorization or ""},
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()



