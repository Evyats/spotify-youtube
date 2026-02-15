# auth-service

Authentication service for signup/signin, email verification, refresh rotation, and Google OAuth callback.

## Env Vars

| Variable | Required | Example |
|---|---|---|
| `DATABASE_URL` | Yes | `postgresql+psycopg://app:app@localhost:5432/spotify_youtube` |
| `JWT_SECRET` | Yes | `dev-secret-change-me` |
| `EMAIL_VERIFY_REQUIRED` | No | `1` |
| `OAUTH_GOOGLE_CLIENT_ID` | No | `your-google-client-id` |
| `OAUTH_GOOGLE_CLIENT_SECRET` | No | `your-google-client-secret` |
| `OAUTH_GOOGLE_REDIRECT_URI` | No | `http://localhost:8000/auth/google/callback` |
| `SERVICE_NAME` | No | `auth-service` |

## Local Setup (No Docker)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
alembic -c alembic.ini upgrade head
```

Set env vars, then run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Networking
- Service listens on `8000`.
- In Docker compose, it is exposed as `8001:8000`.

## Endpoint
- `GET /health`
