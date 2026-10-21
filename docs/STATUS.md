# Status

The claims pilot from `docs/PLAN.md` is built. All six phases are done.

## What's built

- `backend/`: FastAPI and SQLite. The database is `backend/undercover.db`, or the path in `UNDERCOVER_DB`. The backend seeds an empty database from `data/` on startup. It serves the claims, policies with their plan's limits, customers, claim history without personal details, the policy wording, the handlers and the agent's instructions (`backend/instructions.md`). It runs the claim workflow: start, record steps, decide, pay and sign off.
- The payment rule lives in the backend: `pay_claim` refuses a payout over $1,000.00 with 403 until a handler signs off, whatever the agent does, and the sign-off makes the payment. A test checks that every operation has an `operation_id`, a one-line docstring and no optional inputs.
- `agent/`: the UnderCover Agent, LangChain's `create_agent` on OpenRouter, using `openai/gpt-6-luna` at low effort or the model in `MODEL_NAME`. `run(claim_id, thread_id)` starts the claim, loads its instructions from the API, and records each message, tool call and tool result as a step. Its tools read the claim, the policy, the claim history and the policy wording, and decide and pay the claim it was given, all through the API.
- `dashboard/`: React, Vite and TypeScript in the UnderCover brand, with light and dark mode following the system setting. The queue (`/`) shows each claim's status, decision and payout, with counts by status. The claim page (`/claims/<id>`) shows the claim in full with its policy and customer, the agent's decision beside the wording of the section it cites, the payment, the agent's steps as they arrive, and a sign-off for a payout over $1,000.00. The instructions page (`/instructions`) shows the agent's instructions, read only. Every page refreshes every 2 seconds.
- `e2e/`: Playwright tests of the queue, the claim page, live steps, the blocked payment, the sign-off and the instructions. They run on their own backend (port 8001), dashboard (port 5174) and database (`e2e/undercover.db`), reseeded on every run, so they never touch the dev data.

## Running it

- `uv sync` and `npm install` install everything
- `npm run dev` starts the backend on port 8000 and the dashboard at http://localhost:5173
- `uv run -m agent` works every waiting or in-progress claim in order, and `uv run -m agent CLM-1001` works one. The backend must be running. To spend nothing, set `MODEL_NAME=openrouter/free` in `.env`.
- `uv run -m backend.seed` resets the claims
- `npm run check` runs every check, and `npm run e2e` runs the end-to-end tests alone

## Not built yet

As the spec says: the claims manual, sign-in, real payments and messages to customers. Nothing in the product reads `data/evals/`.
