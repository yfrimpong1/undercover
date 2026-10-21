# Status

The claims pilot from `docs/PLAN.md`, in progress. Phases 1 to 5 are done.

- `backend/`: FastAPI and SQLite. The database is `backend/undercover.db`, or the path in `UNDERCOVER_DB`. The backend seeds an empty database on startup, and `uv run -m backend.seed` resets it from `data/`. It serves the claims, policies, customers, claim history, policy wording, handlers and the agent's instructions (`backend/instructions.md`), and runs the claim workflow: start, record steps, decide, pay and sign off. A payout over $1,000.00 gets 403 from `pay_claim` until a handler signs off, and the sign-off makes the payment.
- `agent/`: the UnderCover Agent, LangChain's `create_agent` on OpenRouter. `run(claim_id, thread_id)` starts the claim, loads its instructions from the API, and records each message, tool call and tool result as a step. Its tools read the claim, the policy, the claim history and the policy wording, and decide and pay the claim it was given, all through the API.
- `dashboard/`: React, Vite and TypeScript in the UnderCover brand, with light and dark mode following the system setting. The queue page (`/`) shows each claim with its status, decision and payout, and counts by status. The claim page (`/claims/<id>`) shows the claim in full with its policy and customer, the agent's decision beside the wording of the section it cites, the payment, the agent's steps as they arrive, and a sign-off for a payout over $1,000.00. The instructions page (`/instructions`) shows the agent's instructions, read only. Every page refreshes every 2 seconds.
- `e2e/`: one test of the queue page

## Running it

- `npm run dev` starts the backend on port 8000 and the dashboard on port 5173
- `uv run -m agent` works every waiting or in-progress claim in order, and `uv run -m agent CLM-1001` works one. The backend must be running.
- `uv run -m backend.seed` resets the claims
- `npm run check` runs every check
