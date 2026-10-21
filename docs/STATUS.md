# Status

The claims pilot from `docs/PLAN.md`, in progress. Phase 1 is done.

- `backend/`: FastAPI and SQLite. The database is `backend/undercover.db`, or the path in `UNDERCOVER_DB`. The backend seeds an empty database on startup, and `uv run -m backend.seed` resets it from `data/`. The read operations are `list_claims`, `get_claim`, `get_policy`, `get_customer`, `get_claim_history`, `get_policy_wording` and `list_handlers`.
- `agent/`: still the skeleton, `run(claim_id, thread_id)` with one tool that calls the health route
- `dashboard/`: still the skeleton, one page that shows whether the backend is up
- `e2e/`: one test of that page

## Running it

- `npm run dev` starts the backend on port 8000 and the dashboard on port 5173
- `uv run -m backend.seed` resets the claims
- `npm run check` runs every check
