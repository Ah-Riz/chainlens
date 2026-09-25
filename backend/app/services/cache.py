from __future__ import annotations

from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import WalletAnalysis


async def upsert_analysis(
    session: AsyncSession,
    address: str,
    summary: str,
    stats: dict,
    structured: dict,
) -> None:
    values = {
        "address": address,
        "summary": summary,
        "stats_json": stats,
        "structured_json": structured,
    }
    stmt = insert(WalletAnalysis).values(**values)
    stmt = stmt.on_duplicate_key_update(
        summary=summary,
        stats_json=stats,
        structured_json=structured,
    )
    await session.execute(stmt)
