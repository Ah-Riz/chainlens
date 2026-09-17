from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
from app.routers.wallets import router as wallets_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        await init_db()
    except Exception:
        # ponytail: API still serves mock path if Postgres is down during local UI work
        pass
    yield


app = FastAPI(
    title="ChainLens",
    description="AI-powered Solana wallet intelligence",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(wallets_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "chainlens", "chain": "solana"}
