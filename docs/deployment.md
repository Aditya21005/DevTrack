# DevTrack AI Container Deployment

## Services

`docker-compose.yml` runs three services:

- `postgres`: PostgreSQL 16 with a named volume for local persistence.
- `api`: FastAPI/Uvicorn backend built from `backend/Dockerfile`.
- `web`: React static build served by Nginx from `frontend/Dockerfile`.

The web container proxies `/api/*` to the FastAPI container and serves React routes with an SPA fallback.

## Environment

Copy `.env.example` to `.env` for local Docker usage and replace all placeholder secrets.
Production should inject these values through the deployment platform or a secret manager, not a committed `.env` file.

Required production secrets:

- `POSTGRES_PASSWORD`
- `DEVTRACK_JWT_ACCESS_SECRET_KEY`
- `DEVTRACK_JWT_REFRESH_SECRET_KEY`
- `GEMINI_API_KEY` when AI features are enabled
- `GITHUB_CLIENT_SECRET` and `GITHUB_TOKEN_ENCRYPTION_KEY` when GitHub integration is enabled

## Local Run

```bash
docker compose up --build
```

Open the app at `http://localhost:3000`.
The API is available at `http://localhost:8000/api`.

## Health Checks

Backend:

- `/health/live`: process liveness.
- `/health/ready`: PostgreSQL readiness check.

Frontend:

- `/health`: Nginx/static-serving liveness.

Compose waits for PostgreSQL to become healthy before starting the API and waits for API readiness before starting the web container.

## Production Shape

For production, prefer managed PostgreSQL and run `api` and `web` as separate deployable services:

- Scale `api` horizontally behind a load balancer.
- Serve `web` through a CDN or edge cache when possible.
- Keep `DEVTRACK_DATABASE_POOL_SIZE` conservative per API replica so total connections stay below the database limit.
- Terminate TLS at the load balancer or ingress.
- Inject secrets through the platform secret store.
- Run migrations as a one-off release job before deploying new API replicas.

## Deployment Notes

The backend image starts with:

```bash
uvicorn devtrack_ai_api.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips '*'
```

The frontend image builds Vite with `VITE_API_BASE_URL=/api` by default, so browser API calls stay same-origin through Nginx.

