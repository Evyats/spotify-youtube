# admin-service

Small internal admin API for inspecting system data.

## Env Vars

| Variable | Required | Example |
|---|---|---|
| `DATABASE_URL` | Yes | `postgresql+psycopg://app:app@localhost:5432/spotify_youtube` |
| `JWT_SECRET` | Yes | `dev-secret-change-me` |
| `SERVICE_NAME` | No | `admin-service` |

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
- In Docker compose, it is exposed as `8006:8000`.

## Endpoint
- `GET /health`
