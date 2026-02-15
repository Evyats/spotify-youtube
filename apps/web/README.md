# web

User-facing FastAPI frontend with routed pages for account, search, and library playback.

## Env Vars

| Variable | Required | Example |
|---|---|---|
| `FRONTEND_INTERNAL_API_BASE` | Yes | `http://api-gateway:8000` |
| `FRONTEND_PUBLIC_API_BASE` | Yes | `http://localhost:8000` |

## Local Setup (No Docker)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

Set env vars, then run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Networking
- Service listens on `8000`.
- In Docker compose, it is exposed as `3000:8000`.

## Endpoint
- `GET /health`
