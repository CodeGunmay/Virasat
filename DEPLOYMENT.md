# Virasat deployment: Netlify + Render + PostgreSQL

This configuration assumes a GitHub repository containing `frontend/`, `backend/` and `netlify.toml` at its root. **Do not deploy the old bundled SQLite sample database as persistent user storage.**

## 1. Render PostgreSQL

Create a PostgreSQL database in the Render dashboard. Choose the region that will also host the backend. Copy its **internal database URL** into the backend's `VIRASAT_DATABASE_URL` environment variable. Treat the URL as a secret. Available plans, prices and retention policies may change, so review them before creating a billed resource.

The backend normalizes `postgres://` and `postgresql://` strings to SQLAlchemy's `postgresql+psycopg://` driver. `psycopg[binary]` is in `requirements.txt`.

## 2. Render FastAPI web service

Connect the GitHub repository and select Python, then set:

| Field | Value |
| --- | --- |
| Root directory | `backend` |
| Build command | `pip install -r requirements.txt` |
| Start command | `python -m db.seed_heritage && uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Health path | `/health` |

Set these service environment variables:

- `VIRASAT_DATABASE_URL`: internal database URL from Render PostgreSQL.
- `VIRASAT_SECRET_KEY`: a long random secret generated independently. Do not check it into GitHub.
- `VIRASAT_CORS_ORIGINS`: exact Netlify frontend origin, e.g. `https://your-virasat.netlify.app` (no trailing slash).

The startup seeder is **idempotent**. It creates missing schema tables and inserts the 29-source-labelled starter sites once, leaving user-created data intact. It does not perform schema migrations for future changes: use Alembic migrations before a later release that changes models.

Confirm that the Render URL responds at `/health` and `/sites`. Do not expose `/docs` publicly with sensitive credentials or example tokens.

## 3. Netlify React frontend

Connect the same repository to Netlify; its root `netlify.toml` sets the `frontend` base directory, build command and `/*` single-page-app rewrite.

Add a **build-time** environment variable:

- `REACT_APP_API_BASE_URL`: exact public Render API origin, e.g. `https://virasat-api.onrender.com`.

Rebuild Netlify whenever the API URL changes. The value is compiled into client assets and must not contain secrets.

## 4. Go-live checks

1. Frontend opens and direct navigation to `/planning` works.
2. `GET /sites` loads diverse heritage entries.
3. Changing duration and interests changes at least some example itineraries.
4. The map renders markers and its "estimated routes" disclaimer.
5. New user registration, login, and "Suggest a site" work.
6. Unauthorized users cannot open the moderation API; provision real moderator accounts with a separate secure administrative workflow.
7. Database content persists across a Render backend restart.
8. Test Chrome Android and Safari iPhone layouts.
9. Record screen walkthrough **after** full verification.

**Known limitations:** Walking times use a conservative geometric detour estimate. Coordinates are sourced from map/monument references and have not been independently field-checked. No site operating hours are marked verified unless backed by a specific current source. The app is not a substitute for local access advice.
