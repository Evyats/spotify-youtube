# search-service

Search service that fetches and ranks YouTube candidates, then returns top 3 results.

## Env Vars

| Variable | Required | Example |
|---|---|---|
| `SERVICE_NAME` | No | `search-service` |

## Local Setup (No Docker)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

Run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Networking
- Service listens on `8000`.
- In Docker compose, it is exposed as `8003:8000`.

## Endpoint
- `GET /health`
