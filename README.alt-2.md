# spotify-youtube (Architecture First)

## System Overview
- Frontend: FastAPI web (`web`) + optional Next.js admin web (`apps/admin-web`)
- Edge API: `api-gateway`
- Domain services: `auth`, `search`, `catalog`, `download`, `stream`, `admin`
- Worker: `download-worker` (Celery)
- Data: PostgreSQL, Redis, MinIO

## Runtime Topology
### Public entrypoints
- `web` on `3000`
- `api-gateway` on `8000`
- `stream-service` on `8005`

### Internal-only services
- `auth-service`
- `catalog-service`
- `search-service`
- `download-service`
- `admin-service`
- `postgres`
- `redis`
- `minio`

### Core flow
1. Browser calls `api-gateway`.
2. Gateway calls downstream `/internal/*` endpoints using `X-Service-Token`.
3. Download jobs are enqueued via Redis/Celery and executed by `download-worker`.
4. Audio is stored in MinIO and streamed through stream endpoints.

## Security Model
### Service-to-service trust
- Short-lived signed internal JWT in `X-Service-Token`
- Receiver validates signature + issuer + audience + expiry

### User session model
- Access token returned by signin/refresh
- Refresh token set as HttpOnly cookie by gateway
- Logout revokes refresh token

### Media access model
- Stream access uses short-lived signed token (not client `user_id` query)

### Hardening controls
- Strict secret validation in strict/prod mode
- Rate limits on signin/signup/search/import
- Security headers/CSP
- Non-root containers

## Local Setup
```bash
cp .env.example .env
docker compose up --build
```

User UI: `http://localhost:3000`  
Gateway: `http://localhost:8000`

## Production Setup (Single VM)
Use compose override:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Prod overlay adds:
- TLS edge proxy (Nginx)
- Only `80/443` exposed
- Internal services not host-exposed
- Secret files mounted from `infra/secrets/*`

Required files:
- `infra/secrets/jwt_secret.txt`
- `infra/secrets/internal_service_secret.txt`
- `infra/secrets/database_url.txt`
- `infra/secrets/tls.crt`
- `infra/secrets/tls.key`

## Interfaces
### Main gateway endpoints
- Auth: `/auth/signup`, `/auth/verify-email`, `/auth/signin`, `/auth/refresh`, `/auth/logout`
- Songs: `/songs/search`, `/songs/import`, `/library`, `/stream/{song_id}`, `/jobs/{job_id}`
- Admin: `/admin/users`, `/admin/songs`, `/admin/jobs`

### Operational endpoints
- `/health` and `/metrics` on services

## Observability and Alerts
Start:
```bash
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

- Prometheus config: `infra/monitoring/prometheus.yml`
- Alert rules: `infra/monitoring/alerts.yml`
- Alertmanager config: `infra/monitoring/alertmanager.yml`

## CI Security Pipeline
Workflow: `.github/workflows/security.yml`
- Python dependency auditing (`pip-audit`)
- Node dependency auditing (`npm audit`)
- Filesystem vulnerability scan (`trivy`)
