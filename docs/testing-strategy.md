# DevTrack AI Testing Strategy

## Goals

DevTrack AI should have fast confidence at three levels:

- Unit tests for pure domain logic, auth security, service helpers, UI components, and state transitions.
- Integration tests for boundaries between service layers, routers, API clients, and mocked external providers.
- CI checks that run on every push and pull request without requiring real production secrets.

## Backend Tests

Location: `backend/tests/backend`

Current coverage:

- Authentication password policy and JWT token handling.
- Refresh-token hashing behavior.
- FastAPI route contract checks for auth and project APIs.

Recommended next backend additions:

- Async repository tests with a disposable PostgreSQL test database.
- Service tests for workspace, project, task, kanban, dashboard, and GitHub integration behavior.
- Alembic migration tests once migrations are present.

## Frontend Tests

Location: `frontend/src/**/__tests__`

Current coverage:

- Auth service mock login behavior.
- Protected route redirect behavior.
- Kanban task move logic and immutability.
- Settings page render and theme state behavior.

Test runner:

```bash
cd frontend
npm run test:run
```

## Integration Tests

Location: `backend/tests/integration`

Current coverage:

- Gemini config loading from environment.
- GitHub token encryption/decryption boundary.

Recommended next integration additions:

- Gemini calls with provider mocked at the client boundary.
- GitHub OAuth state completion with mocked GitHub API responses.
- End-to-end API tests against a FastAPI app factory once the app entrypoint exists.

## Authentication Tests

Authentication test priorities:

- Password complexity validation.
- Password hashing and verification.
- Access token and refresh token claim validation.
- Refresh token rotation and family revocation.
- Protected-route behavior on backend and frontend.

## API Tests

API test priorities:

- Route contract existence and status-code mapping.
- Request/response schema validation.
- Permission failures for unauthenticated or non-member users.
- Tenant isolation by workspace/organization id.

## CI

Workflow: `.github/workflows/ci.yml`

Backend CI:

```bash
cd backend
pip install -r requirements-dev.txt
pytest tests/backend tests/integration
```

Frontend CI:

```bash
cd frontend
npm ci
npm run test:run
npm run build
```

Secrets:

- CI must not use real Gemini or GitHub keys by default.
- Provider calls should be mocked unless running an explicitly approved smoke workflow.
- Local `.env` files must stay ignored.

## Coverage Policy

Initial target:

- Backend domain/security logic: 80%+ for touched modules.
- Frontend feature logic/hooks/components: 70%+ for touched feature slices.
- Critical auth and tenant isolation paths: required coverage before production release.

## Release Gate

A production release should require:

- Backend tests pass.
- Frontend tests pass.
- Frontend production build passes.
- No real secrets committed.
- Any external AI/GitHub tests either mocked or explicitly marked as smoke tests.


