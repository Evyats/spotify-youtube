# spotify-youtube

Python-first microservices MVP for a Spotify-like app with YouTube search/import flow.

## Implemented phases
1. Foundation: microservices + persistent Docker data folders + Git repo.
2. Search MVP: YouTube search endpoint with ranking and top-3 selection.
3. Download MVP: async job creation in `download-service` and Celery worker pipeline.
4. Playback MVP: range-capable stream endpoint backed by MinIO object storage.
5. Admin MVP: admin-protected endpoints for users/songs/jobs via gateway.
6. Hardening: Alembic migrations, refresh-token rotation store, email verification flow, Google OAuth wiring, metrics endpoint.

## Stack
- FastAPI services
- Celery + Redis queue
- PostgreSQL via SQLAlchemy
- Alembic for schema migrations
- MinIO (S3-compatible) for audio objects
- Next.js web + admin-web apps
- Docker Compose local orchestration

## Local persistent data
- `infra/docker/data/postgres`
- `infra/docker/data/redis`
- `infra/docker/data/minio`

These folders keep data between container restarts.

## Run
```bash
docker compose up --build
```

## Frontends
```bash
cd apps/web && npm install && npm run dev
cd apps/admin-web && npm install && npm run dev
```

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
