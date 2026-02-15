# download-worker

Background Celery worker that performs media download, transcode, upload, and finalize steps.

## Env Vars

| Variable | Required | Example |
|---|---|---|
| `DATABASE_URL` | Yes | `postgresql+psycopg://app:app@localhost:5432/spotify_youtube` |
| `CELERY_BROKER_URL` | Yes | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Yes | `redis://localhost:6379/1` |
| `S3_ENDPOINT` | Yes | `http://localhost:9000` |
| `S3_ACCESS_KEY` | Yes | `minioadmin` |
| `S3_SECRET_KEY` | Yes | `minioadmin` |
| `S3_BUCKET` | Yes | `songs` |

## Local Setup (No Docker)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

Set env vars, then run:

```bash
celery -A app.worker:celery_app worker --loglevel=info
```

## Networking
- No HTTP port (worker process only).
- Uses Redis, Postgres, and object storage over network.

## Endpoint
- Not applicable (no HTTP API)
