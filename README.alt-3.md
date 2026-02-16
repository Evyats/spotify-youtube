# spotify-youtube (Ops Playbook)

## 1. Local Bring-up
### 1.1 Prepare env
```bash
cp .env.example .env
```
Windows `cmd`:
```cmd
copy .env.example .env
```

### 1.2 Start stack
```bash
docker compose up --build
```

### 1.3 Verify
- User app: `http://localhost:3000`
- API gateway health: `http://localhost:8000/health`

## 2. Common Commands
### Start detached
```bash
docker compose up -d
```

### Rebuild one service
```bash
docker compose up -d --build api-gateway
```

### Stop all
```bash
docker compose down
```

## 3. Admin UI
Run separately:
```bash
cd apps/admin-web
npm install
npm run dev
```
Open `http://localhost:3001`.

## 4. Ports
- `3000` user app
- `8000` API gateway
- `8005` stream endpoint

All other services are internal network only.

## 5. Production Deployment
### 5.1 Create required secret files
- `infra/secrets/jwt_secret.txt`
- `infra/secrets/internal_service_secret.txt`
- `infra/secrets/database_url.txt`
- `infra/secrets/tls.crt`
- `infra/secrets/tls.key`

### 5.2 Start prod overlay
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 5.3 What prod overlay changes
- Adds TLS edge proxy (`edge`)
- Exposes only `80/443`
- Routes `/api/*` to `api-gateway`
- Routes `/api/public/stream/*` to `stream-service`
- Applies basic edge abuse controls

## 6. Monitoring
Start monitoring:
```bash
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

- Prometheus: `http://localhost:9090`
- Alertmanager: `http://localhost:9093`

## 7. Security Baseline
- Internal service auth with `X-Service-Token`
- Refresh token in HttpOnly cookie
- Signed short-lived stream tokens
- Rate limiting on high-risk endpoints
- Non-root service containers
- Strict secret checks in strict/prod mode

## 8. API Quick Reference
- `POST /auth/signup`
- `POST /auth/verify-email`
- `POST /auth/signin`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /songs/search`
- `POST /songs/import`
- `GET /library`
- `GET /stream/{song_id}`
- `GET /jobs/{job_id}`
- `GET /admin/users`
- `GET /admin/songs`
- `GET /admin/jobs`

## 9. CI Security Checks
Workflow: `.github/workflows/security.yml`
- `pip-audit`
- `npm audit`
- `trivy`
