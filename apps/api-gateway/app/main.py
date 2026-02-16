import os

import httpx
from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware

from packages.shared.schemas import ImportSongRequest, RefreshRequest, SignInRequest, SignUpRequest, VerifyEmailRequest
from packages.shared.internal_auth import create_service_token
from packages.shared.rate_limit import InMemoryRateLimiter
from packages.shared.security import decode_token, validate_security_runtime


app = FastAPI(title="api-gateway")
from packages.shared.observability import register_observability
register_observability(app, app.title)
validate_security_runtime()

def env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value if value else default


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


raw_cors = env_str(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
)
allowed_origins = [o.strip() for o in raw_cors.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Service-Token"],
)

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
SEARCH_SERVICE_URL = os.getenv("SEARCH_SERVICE_URL", "http://search-service:8000")
DOWNLOAD_SERVICE_URL = os.getenv("DOWNLOAD_SERVICE_URL", "http://download-service:8000")
CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://catalog-service:8000")
STREAM_SERVICE_URL = os.getenv("STREAM_SERVICE_URL", "http://stream-service:8000")
ADMIN_SERVICE_URL = os.getenv("ADMIN_SERVICE_URL", "http://admin-service:8000")
API_GATEWAY_SERVICE_NAME = os.getenv("API_GATEWAY_SERVICE_NAME", "api-gateway")

REFRESH_COOKIE_NAME = env_str("REFRESH_COOKIE_NAME", "refresh_token")
REFRESH_COOKIE_SECURE = os.getenv("REFRESH_COOKIE_SECURE", "0").lower() in {"1", "true", "yes", "on"}
REFRESH_COOKIE_DOMAIN = os.getenv("REFRESH_COOKIE_DOMAIN") or None
REFRESH_COOKIE_SAMESITE = env_str("REFRESH_COOKIE_SAMESITE", "lax")
REFRESH_COOKIE_MAX_AGE = env_int("REFRESH_COOKIE_MAX_AGE_SECONDS", 14 * 24 * 3600)

SIGNIN_IP_LIMIT = env_int("RATE_LIMIT_SIGNIN_IP_PER_MIN", 20)
SIGNIN_EMAIL_LIMIT = env_int("RATE_LIMIT_SIGNIN_EMAIL_PER_MIN", 10)
SIGNUP_IP_LIMIT = env_int("RATE_LIMIT_SIGNUP_IP_PER_HOUR", 30)
SEARCH_USER_LIMIT = env_int("RATE_LIMIT_SEARCH_PER_MIN", 120)
IMPORT_USER_LIMIT = env_int("RATE_LIMIT_IMPORT_PER_HOUR", 120)
limiter = InMemoryRateLimiter()


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


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    return response


def request_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def enforce_rate_limit(key: str, limit: int, window_seconds: int) -> None:
    if limiter.check(key, limit, window_seconds):
        return
    raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="rate limit exceeded")


def service_headers(target_service: str, extra_headers: dict[str, str] | None = None) -> dict[str, str]:
    headers = {"X-Service-Token": create_service_token(API_GATEWAY_SERVICE_NAME, target_service)}
    if extra_headers:
        headers.update(extra_headers)
    return headers


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=REFRESH_COOKIE_SECURE,
        samesite=REFRESH_COOKIE_SAMESITE,  # type: ignore[arg-type]
        max_age=REFRESH_COOKIE_MAX_AGE,
        path="/",
        domain=REFRESH_COOKIE_DOMAIN or None,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        secure=REFRESH_COOKIE_SECURE,
        samesite=REFRESH_COOKIE_SAMESITE,  # type: ignore[arg-type]
        path="/",
        domain=REFRESH_COOKIE_DOMAIN or None,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api-gateway"}


@app.post("/auth/signup")
async def signup(payload: SignUpRequest, request: Request):
    ip = request_ip(request)
    enforce_rate_limit(f"signup:ip:{ip}", SIGNUP_IP_LIMIT, 3600)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{AUTH_SERVICE_URL}/internal/signup",
            json=payload.model_dump(),
            headers=service_headers("auth-service"),
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


@app.post("/auth/verify-email")
async def verify_email(payload: VerifyEmailRequest):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{AUTH_SERVICE_URL}/internal/verify-email",
            json=payload.model_dump(),
            headers=service_headers("auth-service"),
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


@app.post("/auth/signin")
async def signin(payload: SignInRequest, request: Request, response: Response):
    ip = request_ip(request)
    enforce_rate_limit(f"signin:ip:{ip}", SIGNIN_IP_LIMIT, 60)
    enforce_rate_limit(f"signin:email:{payload.email.lower()}", SIGNIN_EMAIL_LIMIT, 60)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{AUTH_SERVICE_URL}/internal/signin",
            json=payload.model_dump(),
            headers=service_headers("auth-service"),
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    data = r.json()
    refresh_token = data.get("refresh_token")
    if refresh_token:
        set_refresh_cookie(response, refresh_token)
    return {"access_token": data.get("access_token"), "token_type": data.get("token_type", "bearer")}


@app.post("/auth/refresh")
async def refresh(
    response: Response,
    payload: RefreshRequest | None = None,
    refresh_cookie: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
):
    refresh_token = refresh_cookie or (payload.refresh_token if payload else None)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing refresh token")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{AUTH_SERVICE_URL}/internal/refresh",
            json={"refresh_token": refresh_token},
            headers=service_headers("auth-service"),
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    data = r.json()
    next_refresh = data.get("refresh_token")
    if next_refresh:
        set_refresh_cookie(response, next_refresh)
    return {"access_token": data.get("access_token"), "token_type": data.get("token_type", "bearer")}


@app.post("/auth/logout")
async def logout(
    response: Response,
    refresh_cookie: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
):
    if refresh_cookie:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{AUTH_SERVICE_URL}/internal/logout",
                json={"refresh_token": refresh_cookie},
                headers=service_headers("auth-service"),
            )
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.json())
    clear_refresh_cookie(response)
    return {"detail": "signed out"}


@app.get("/auth/google/login")
async def google_login():
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{AUTH_SERVICE_URL}/internal/oauth/google/login",
            headers=service_headers("auth-service"),
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


@app.get("/auth/google/callback")
async def google_callback(code: str, state: str, response: Response):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{AUTH_SERVICE_URL}/internal/oauth/google/callback",
            params={"code": code, "state": state},
            headers=service_headers("auth-service"),
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    data = r.json()
    refresh_token = data.get("refresh_token")
    if refresh_token:
        set_refresh_cookie(response, refresh_token)
    return {"access_token": data.get("access_token"), "token_type": data.get("token_type", "bearer")}


@app.get("/songs/search")
async def search(q: str, claims: dict = Depends(bearer_token_dep)):
    enforce_rate_limit(f"search:user:{claims.get('sub')}", SEARCH_USER_LIMIT, 60)
    req = {"query": q, "user_id": claims.get("sub")}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{SEARCH_SERVICE_URL}/internal/search",
            json=req,
            headers=service_headers("search-service"),
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


@app.post("/songs/import")
async def import_song(payload: ImportSongRequest, claims: dict = Depends(bearer_token_dep)):
    enforce_rate_limit(f"import:user:{claims.get('sub')}", IMPORT_USER_LIMIT, 3600)
    req = {
        "user_id": claims.get("sub"),
        "source_provider": payload.source_provider,
        "source_video_id": payload.source_id,
        "title": payload.title,
        "artist": payload.artist,
        "candidate_meta": payload.candidate_meta,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{DOWNLOAD_SERVICE_URL}/internal/jobs",
            json=req,
            headers=service_headers("download-service"),
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


@app.get("/library")
async def library(claims: dict = Depends(bearer_token_dep)):
    user_id = claims.get("sub")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{CATALOG_SERVICE_URL}/internal/library/{user_id}",
            headers=service_headers("catalog-service"),
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


@app.get("/stream/{song_id}")
async def stream(song_id: str, claims: dict = Depends(bearer_token_dep)):
    user_id = claims.get("sub")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{STREAM_SERVICE_URL}/internal/stream-url/{song_id}",
            params={"user_id": user_id},
            headers=service_headers("stream-service"),
        )
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
        r = await client.get(
            f"{DOWNLOAD_SERVICE_URL}/internal/jobs/{job_id}",
            params={"user_id": user_id},
            headers=service_headers("download-service"),
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


@app.get("/admin/users")
async def admin_users(_: dict = Depends(require_admin), authorization: str | None = Header(default=None, alias="Authorization")):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{ADMIN_SERVICE_URL}/internal/admin/users",
            headers=service_headers("admin-service", {"Authorization": authorization or ""}),
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


@app.get("/admin/songs")
async def admin_songs(_: dict = Depends(require_admin), authorization: str | None = Header(default=None, alias="Authorization")):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{ADMIN_SERVICE_URL}/internal/admin/songs",
            headers=service_headers("admin-service", {"Authorization": authorization or ""}),
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


@app.get("/admin/jobs")
async def admin_jobs(_: dict = Depends(require_admin), authorization: str | None = Header(default=None, alias="Authorization")):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{ADMIN_SERVICE_URL}/internal/admin/jobs",
            headers=service_headers("admin-service", {"Authorization": authorization or ""}),
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()



