# DevTrack AI

DevTrack AI is an AI-powered developer productivity platform that combines project tracking, Kanban workflows, GitHub activity, dashboard analytics, and AI-assisted planning/documentation for engineering teams.

The product is being built as a production-style SaaS application with a FastAPI backend, PostgreSQL persistence, a React frontend, Docker-based local orchestration, and CI-ready tests.

## What It Does

DevTrack AI is intended to help teams:

- Manage workspaces, members, roles, and invitations.
- Create and track projects with status, deadlines, and priority.
- Manage tasks with assignments, labels, comments, attachments, dependencies, status, and progress.
- Move tasks across Kanban boards with backend ordering support.
- View dashboard analytics for productivity, pending/completed work, charts, and monthly statistics.
- Use Gemini-powered AI for task breakdowns, documentation generation, sprint planning, and daily summaries.
- Connect GitHub for repositories, commits, issues, pull requests, and metadata sync.

## Tech Stack

### Backend

- FastAPI
- SQLAlchemy 2
- PostgreSQL
- Pydantic / Pydantic Settings
- JWT authentication
- Argon2 password hashing
- Alembic planned for migrations
- Pytest for backend tests

### Frontend

- Vite
- React 18
- TypeScript
- React Router v6 data router
- TanStack Query
- Zustand
- React Hook Form
- Zod
- Tailwind CSS
- shadcn-style UI primitives
- Axios
- Vitest / Testing Library

### Infrastructure

- Docker
- Docker Compose
- Nginx for frontend static hosting and `/api` proxying
- GitHub Actions CI

## Project Structure

```text
DevTrazk/
  .github/
    workflows/
      ci.yml
  backend/
    devtrack_ai_api/             # FastAPI app entrypoint and exception handlers
    devtrack_ai_auth/            # Authentication models, routes, services, schemas
    devtrack_ai_workspace/       # Workspace/member/role management
    devtrack_ai_projects/        # Project management
    devtrack_ai_tasks/           # Task management
    devtrack_ai_kanban/          # Kanban board operations
    devtrack_ai_dashboard/       # Analytics/dashboard APIs
    devtrack_ai_ai/              # Gemini service and AI workflows
    devtrack_ai_integrations/    # GitHub integration services
    devtrack_ai_db/              # Database config, session, shared models, access control
    tests/                       # Backend and integration tests
    Dockerfile
    requirements.txt
    requirements-dev.txt
    pytest.ini
  frontend/
    src/
      app/                       # Providers and router
      components/                # Shared UI/layout components
      features/                  # Feature-based frontend modules
      layouts/                   # Public/auth/dashboard layouts
      lib/                       # Axios client, runtime config, helpers
      store/                     # UI-only global state
      theme/                     # Theme tokens
    Dockerfile
    nginx.conf
    package.json
  docs/
    database-design.md
    deployment.md
    testing-strategy.md
  docker-compose.yml
  .env.example
  .env.production.example
```

## Prerequisites

Install these tools before running the project locally:

- Node.js 24+
- npm
- Docker Desktop
- Python 3.12+ for backend development and tests
- PostgreSQL if running the backend without Docker

Docker is the easiest way to run the full stack.

## Environment Setup

Copy the example environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Then update the values in `.env`.

Important variables:

```text
POSTGRES_DB=devtrack_ai
POSTGRES_USER=devtrack
POSTGRES_PASSWORD=change-this-local-password

DEVTRACK_ENVIRONMENT=production
DEVTRACK_DATABASE_URL=postgresql+psycopg://devtrack:change-this-local-password@postgres:5432/devtrack_ai
DEVTRACK_JWT_ACCESS_SECRET_KEY=replace-with-32-plus-character-access-secret
DEVTRACK_JWT_REFRESH_SECRET_KEY=replace-with-32-plus-character-refresh-secret
DEVTRACK_CORS_ALLOWED_ORIGINS=http://localhost:3000

VITE_API_BASE_URL=/api
VITE_USE_MOCK_API=false

GEMINI_API_KEY=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_REDIRECT_URI=http://localhost:3000/integrations/github/callback
GITHUB_TOKEN_ENCRYPTION_KEY=replace-with-32-plus-character-token-key
```

Never commit real `.env` files or production secrets.

## Run With Docker

From the project root:

```bash
docker compose up --build
```

App URLs:

```text
Frontend: http://localhost:3000
Backend:  http://localhost:8000/api
Health:   http://localhost:8000/health/ready
```

The Docker setup starts:

- `postgres` on port `5432`
- `api` on port `8000`
- `web` on port `3000`

The frontend container serves the Vite production build through Nginx and proxies `/api` requests to the backend container.

## Run Frontend Locally

```bash
cd frontend
npm install
npm run dev
```

By default, development mode can use mock frontend data. To force real backend calls, set:

```bash
VITE_USE_MOCK_API=false
```

Then open:

```text
http://localhost:5173
```

## Run Backend Locally

Install backend dependencies:

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
```

On Windows PowerShell:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Run the FastAPI app:

```bash
uvicorn devtrack_ai_api.main:app --reload --host 0.0.0.0 --port 8000
```

Backend health endpoints:

```text
GET /health/live
GET /health/ready
```

API routes are mounted under `/api`.

## Tests

### Frontend Tests

```bash
cd frontend
npm run test:run
npm run build
```

### Backend Tests

```bash
cd backend
pytest tests/backend tests/integration
```

Backend tests require Python 3.12+ and the packages from `requirements-dev.txt`.

## CI

GitHub Actions workflow:

```text
.github/workflows/ci.yml
```

CI runs:

- Backend dependency install and pytest from `backend/`
- Frontend dependency install, tests, and production build from `frontend/`

## Docker Notes

Backend image:

```text
backend/Dockerfile
```

Frontend image:

```text
frontend/Dockerfile
```

Compose file:

```text
docker-compose.yml
```

Validate Compose config:

```bash
docker compose config --quiet
```

## Production Notes

Before production deployment, complete these items:

- Add Alembic migrations and migration release jobs.
- Replace local secrets with a secret manager.
- Use managed PostgreSQL.
- Enable HTTPS at the load balancer or ingress.
- Add request tracing, metrics, and centralized logging.
- Add API rate limiting and request-size limits.
- Finish real frontend/backend contract alignment for every feature.
- Add background workers for long-running AI and GitHub sync work.
- Add full backend integration tests against disposable PostgreSQL.

## Useful Commands

```bash
# Start full stack
docker compose up --build

# Validate Docker Compose
docker compose config --quiet

# Frontend tests
cd frontend && npm run test:run

# Frontend production build
cd frontend && npm run build

# Backend tests
cd backend && pytest tests/backend tests/integration

# Run backend locally
cd backend && uvicorn devtrack_ai_api.main:app --reload --port 8000
```

## Current Status

The project has a clean high-level layout:

- Backend code is grouped under `backend/`.
- Frontend code is grouped under `frontend/`.
- Root contains only orchestration, docs, environment templates, and CI config.

Frontend tests and production build are passing. Docker Compose config validates. Backend tests require a local Python installation.
