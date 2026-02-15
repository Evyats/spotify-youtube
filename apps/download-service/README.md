# download-service

Download orchestration service that creates import jobs and queues worker tasks.

## Env Vars

| Variable | Required | Example |
|---|---|---|
| `DATABASE_URL` | Yes | `postgresql+psycopg://app:app@localhost:5432/spotify_youtube` |
| `CELERY_BROKER_URL` | Yes | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Yes | `redis://localhost:6379/1` |
| `SERVICE_NAME` | No | `download-service` |

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
- In Docker compose, it is exposed as `8004:8000`.

## Endpoint
- `GET /health`
