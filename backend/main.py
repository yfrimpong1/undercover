"""The UnderCover backend."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, closing

from fastapi import FastAPI

from backend import claims, records
from backend.db import connect
from backend.seed import seed_if_empty


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Seed an empty database when the backend starts."""
    with closing(connect()) as db, db:
        seed_if_empty(db)
    yield


app = FastAPI(title="UnderCover", lifespan=lifespan)
app.include_router(claims.router)
app.include_router(records.router)


@app.get("/api/health", operation_id="health")
def health() -> dict[str, str]:
    """Check that the backend is running."""
    return {"status": "ok"}
