# Status

The claims pilot from `docs/PLAN.md`, in progress. Phases 1 and 2 are done.

- `backend/`: FastAPI and SQLite. The database is `backend/undercover.db`, or the path in `UNDERCOVER_DB`. The backend seeds an empty database on startup, and `uv run -m backend.seed` resets it from `data/`. It serves the claims, policies, customers, claim history, policy wording, handlers and the agent's instructions (`backend/instructions.md`), and runs the claim workflow: start, record steps, decide, pay and sign off. A payout over $1,000.00 gets 403 from `pay_claim` until a handler signs off, and the sign-off makes the payment.
- `agent/`: still the skeleton, `run(claim_id, thread_id)` with one tool that calls the health route
- `dashboard/`: still the skeleton, one page that shows whether the backend is up
- `e2e/`: one test of that page

## Running it

- `npm run dev` starts the backend on port 8000 and the dashboard on port 5173
- `uv run -m backend.seed` resets the claims
- `npm run check` runs every check
