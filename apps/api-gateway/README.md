# api-gateway

Public API gateway that routes client requests to backend services and enforces auth checks.

## Env Vars

| Variable | Required | Example |
|---|---|---|
| `JWT_SECRET` | Yes | `dev-secret-change-me` |
| `AUTH_SERVICE_URL` | Yes | `http://auth-service:8000` |
| `SEARCH_SERVICE_URL` | Yes | `http://search-service:8000` |
| `DOWNLOAD_SERVICE_URL` | Yes | `http://download-service:8000` |
| `CATALOG_SERVICE_URL` | Yes | `http://catalog-service:8000` |
| `STREAM_SERVICE_URL` | Yes | `http://stream-service:8000` |
| `ADMIN_SERVICE_URL` | Yes | `http://admin-service:8000` |

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
- In Docker compose, it is exposed as `8000:8000`.

## Endpoint
- `GET /health`
