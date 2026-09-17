from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
from app.routers.wallets import router as wallets_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        await init_db()
    except Exception:
        # API still serves analyze without TiDB; similarity/cache need a healthy DB.
        logger.exception("init_db failed — persistence and similarity unavailable")
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
