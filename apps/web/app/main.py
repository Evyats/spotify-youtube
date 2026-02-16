import os
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="web-frontend")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

INTERNAL_API_BASE = os.getenv("FRONTEND_INTERNAL_API_BASE", "http://api-gateway:8000")
PUBLIC_API_BASE = os.getenv("FRONTEND_PUBLIC_API_BASE", "http://localhost:8000")


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "img-src 'self' data:; "
        "media-src 'self' http://localhost:8005 http://127.0.0.1:8005; "
        f"connect-src 'self' {PUBLIC_API_BASE} http://localhost:8000 http://127.0.0.1:8000; "
        "frame-ancestors 'none'"
    )
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "web-frontend"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(str(BASE_DIR / "static" / "favicon.svg"), media_type="image/svg+xml")


@app.get("/")
async def home(request: Request):
    gateway_ok = False
    try:
        async with httpx.AsyncClient(timeout=2.5) as client:
            resp = await client.get(f"{INTERNAL_API_BASE}/health")
            gateway_ok = resp.status_code == 200
    except Exception:
        gateway_ok = False

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"api_base": PUBLIC_API_BASE, "gateway_ok": gateway_ok, "active_page": "home"},
    )


@app.get("/search")
async def search_page(request: Request):
    gateway_ok = False
    try:
        async with httpx.AsyncClient(timeout=2.5) as client:
            resp = await client.get(f"{INTERNAL_API_BASE}/health")
            gateway_ok = resp.status_code == 200
    except Exception:
        gateway_ok = False

    return templates.TemplateResponse(
        request=request,
        name="search.html",
        context={"api_base": PUBLIC_API_BASE, "gateway_ok": gateway_ok, "active_page": "search"},
    )


@app.get("/library")
async def library_page(request: Request):
    gateway_ok = False
    try:
        async with httpx.AsyncClient(timeout=2.5) as client:
            resp = await client.get(f"{INTERNAL_API_BASE}/health")
            gateway_ok = resp.status_code == 200
    except Exception:
        gateway_ok = False

    return templates.TemplateResponse(
        request=request,
        name="library.html",
        context={"api_base": PUBLIC_API_BASE, "gateway_ok": gateway_ok, "active_page": "library"},
    )
