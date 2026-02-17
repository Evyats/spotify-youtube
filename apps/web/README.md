# web

Main user frontend built with Vite + React + TypeScript + Tailwind.

## Env Vars

| Variable | Required | Example |
|---|---|---|
| `VITE_API_BASE_URL` | Yes | `http://localhost:8000` |

## Local Setup (No Docker)

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Build

```bash
npm run build
```

## Docker
- Local dev compose runs Vite dev server and exposes `3000:3000`.
- Production compose override builds static assets and serves them via Nginx on internal port `80`.
