# catalog-service

Catalog service for songs metadata and user library mapping.

## Env Vars

| Variable | Required | Example |
|---|---|---|
| `DATABASE_URL` | Yes | `postgresql+psycopg://app:app@localhost:5432/spotify_youtube` |
| `SERVICE_NAME` | No | `catalog-service` |

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
- In Docker compose, it is exposed as `8002:8000`.

## Endpoint
- `GET /health`
