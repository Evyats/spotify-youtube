# stream-service

Streaming service that validates ownership and serves audio byte-range playback URLs/data.

## Env Vars

| Variable | Required | Example |
|---|---|---|
| `DATABASE_URL` | Yes | `postgresql+psycopg://app:app@localhost:5432/spotify_youtube` |
| `S3_ENDPOINT` | Yes | `http://localhost:9000` |
| `S3_ACCESS_KEY` | Yes | `minioadmin` |
| `S3_SECRET_KEY` | Yes | `minioadmin` |
| `S3_BUCKET` | Yes | `songs` |
| `PUBLIC_STREAM_BASE` | Yes | `http://localhost:8005` |
| `SERVICE_NAME` | No | `stream-service` |

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
- In Docker compose, it is exposed as `8005:8000`.

## Endpoint
- `GET /health`
