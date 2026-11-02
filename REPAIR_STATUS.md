# Virasat — Independent Repair Status

This is a targeted repair of the Arena export, **not** a claim that the entire PRD is complete.

## Corrected and tested

- React Router now wraps all navigation hooks.
- Planning form reads `GET /sites` (`items`) and calls `POST /plans` using its actual schema.
- Shared typed plan state connects planning, itinerary timeline, map and replanning.
- Leaflet is initialized once per mount and uses backend site coordinates.
- Map shows selected stops and displays a disclaimer when route geometry is approximate.
- Backend request validators, response types, request-scoped DB session and missing dependencies repaired.
- A conservative time-budget planner replaces the defective original selection path.
- Replanning uses current position/time, visited/skipped IDs, and calculates a diff.
- Ten isolated backend acceptance tests pass, including login/JWT authorization, protected site submissions, moderator approval, schedule restrictions, walking-leg and rest constraints, and deterministic time-budget invariants across 100 varied inputs.
- One React landing-page test passes; the optimized frontend build passes without lint warnings.
- The obsolete landing-page API flow was replaced with the live `GET /sites` contract, and the map popup no longer interpolates untrusted names as HTML.
- Mid-walk replanning now accepts an explicitly selected current landmark or user-initiated GPS position.
- An idempotent seeder creates **29 source-labelled Ahmedabad sites** in a separate demo database or PostgreSQL; old Arena user databases are excluded from shareable release ZIPs.
- `netlify.toml` and `DEPLOYMENT.md` document frontend hosting, Render FastAPI, PostgreSQL and production environment variables.
- Opening-hours filters exclude unverified hours; category filtering matches individual category tags rather than JSON-array equality.
- Weekday/date-specific site restrictions now read the actual `weekday_or_date` database column.
- Browser API access now defaults to localhost origins; configure `VIRASAT_CORS_ORIGINS` on deployment.
- Registration and login screens send real requests, and session-scoped JWT credentials are attached to protected API calls. Public registration cannot grant moderator privileges.
- The community contribution form accepts source-backed heritage sites, persists them as pending records, and displays each contributor's review status. Moderation approval creates a site; visitors are forbidden from moderating.
- Frontend production build passes; see build output for any non-blocking lint warnings.

## Important limitations — do not hide during judging

1. The *old Arena* SQLite database contains three sample locations and possible user accounts; it is preserved locally but excluded from release archives. The **new** starter dataset has 29 source-labelled places, all with **low coordinate confidence** pending field verification. Several locations are protected monuments with restricted visitor access, which must be checked independently.
2. The walking-time method uses Haversine distance × 3.5 detour factor. It is an **estimate**, not a verified pedestrian-route matrix. The returned map line is a point-to-point approximation.
3. No opening schedules have been verified for the new 29 places; plans explicitly flag `hours_unverified`. The app must not advertise guaranteed access or opening hours.
4. Authentication, submissions and moderator approval have isolated API tests; saved routes, other legacy screens, complete moderator dashboard and multilingual UI still need review. No publicly registered user can become a moderator; provisioning requires a secure administrative workflow.
5. No real browser end-to-end test, deployment verification, optimizer-vs-baseline quality benchmark, or external network map-tile validation has yet been performed. The 100-input test checks invariants and determinism, **not** optimizer superiority.
6. The planner is greedy, deterministic and budget-aware; it does **not** claim optimality. It now enforces leg caps and rest budgets, but broader route restrictions and real pedestrian navigation are not complete.

## Run locally

Backend (Python 3.11+):

```
cd virasat/backend
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m db.seed_heritage
.venv/bin/python -m pytest -q tests
.venv/bin/uvicorn main:app --port 8000
```

Frontend (Node.js):

```
cd virasat/frontend
npm ci
cp .env.example .env
npm start
```

Use `npm run build` to produce a production bundle. Make sure `REACT_APP_API_BASE_URL` points to the reachable backend URL.

## Next critical steps

Verify and expand heritage data; source genuine walking routes; review moderator workflows and persistent sessions; add full browser E2E coverage; implement the PRD's remaining screens and benchmark; deploy and test on mobile.

See `HERITAGE_DATA_AUDIT.md` for official sources, field-level provenance policy and a release checklist.
