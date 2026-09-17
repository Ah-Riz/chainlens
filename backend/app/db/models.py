from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from tidb_vector.sqlalchemy import VectorType

from app.config import settings

# #region agent log
try:
    import json as _json
    import time as _time

    _p = {
        "sessionId": "6a98e1",
        "hypothesisId": "A",
        "location": "models.py:create_async_engine",
        "message": "creating engine",
        "data": {"scheme": settings.database_url_scheme},
        "timestamp": int(_time.time() * 1000),
    }
    print(f"[chainlens-debug] {_p}", flush=True)
except Exception:
    pass
# #endregion

# TiDB Cloud: mysql+asyncmy://user:pass@gateway/db?ssl=true
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


class WalletAnalysis(Base):
    __tablename__ = "wallet_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    address: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    summary: Mapped[str] = mapped_column(Text)
    stats_json: Mapped[dict] = mapped_column(JSON, default=dict)
    structured_json: Mapped[dict] = mapped_column(JSON, default=dict)
    embedding = mapped_column(VectorType(1536), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"
    __table_args__ = (UniqueConstraint("signature", name="uq_wallet_tx_signature"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    address: Mapped[str] = mapped_column(String(64), index=True)
    signature: Mapped[str] = mapped_column(String(128))
    slot: Mapped[int | None] = mapped_column(Integer, nullable=True)
    block_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tx_type: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    programs: Mapped[list] = mapped_column(JSON, default=list)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
