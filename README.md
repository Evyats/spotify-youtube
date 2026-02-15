# spotify-youtube

Python-first microservices MVP for a Spotify-like app with YouTube search/import flow.


## Stack
- FastAPI services
- Celery + Redis queue
- PostgreSQL via SQLAlchemy
- Alembic for schema migrations
- MinIO (S3-compatible) for audio objects
- FastAPI web frontend + optional Next.js admin scaffold
- Docker Compose local orchestration

## Local persistent data
- `infra/docker/data/postgres`
- `infra/docker/data/redis`
- `infra/docker/data/minio`

These folders keep data between container restarts.

## Environment File
Before starting the app, create a local `.env` file from the template:

```bash
cp .env.example .env
```

Windows `cmd`:

```cmd
copy .env.example .env
```

Then edit `.env` and set your real values (especially secrets like `JWT_SECRET`, DB credentials, and OAuth keys if used).

## Run
```bash
docker compose up --build
```

## Frontends
- User frontend is now FastAPI + Uvicorn at `http://localhost:3000` (served by `web` service in Docker Compose).
- Admin frontend remains in `apps/admin-web` (Next.js scaffold) if you want a separate admin UI later.

## Main gateway API (`http://localhost:8000`)
- `POST /auth/signup`
- `POST /auth/verify-email`
- `POST /auth/signin`
- `POST /auth/refresh`
- `GET /auth/google/login`
- `GET /auth/google/callback`
- `GET /songs/search?q=...` (requires bearer token)
- `POST /songs/import` (requires bearer token)
- `GET /library` (requires bearer token)
- `GET /jobs/{job_id}` (requires bearer token)
- `GET /stream/{song_id}` (requires bearer token; redirects to stream URL)
- `GET /admin/users` (admin token)
- `GET /admin/songs` (admin token)
- `GET /admin/jobs` (admin token)

## Notes
- First signed-up user is assigned `admin` role automatically.
- With `EMAIL_VERIFY_REQUIRED=1`, users must verify email before signin.
- In dev, signup response includes verification token (email delivery service not yet added).
- Worker uses `yt-dlp` and `ffmpeg` to fetch/transcode audio to AAC 256kbps.
- YouTube download/storage legal and platform-policy review is required before production.
