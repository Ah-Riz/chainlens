from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import WalletAnalysis, WalletTransaction
from app.schemas import SimilarAnalysisItem
from app.services.solana.decoder import ActivityEvent


async def upsert_analysis(
    session: AsyncSession,
    address: str,
    summary: str,
    stats: dict,
    structured: dict,
    embedding: list[float] | None,
) -> None:
    values = {
        "address": address,
        "summary": summary,
        "stats_json": stats,
        "structured_json": structured,
        "embedding": embedding,
    }
    stmt = insert(WalletAnalysis).values(**values)
    stmt = stmt.on_duplicate_key_update(
        summary=summary,
        stats_json=stats,
        structured_json=structured,
        embedding=embedding,
    )
    await session.execute(stmt)


async def upsert_transactions(
    session: AsyncSession,
    address: str,
    events: list[ActivityEvent],
) -> None:
    for e in events:
        stmt = insert(WalletTransaction).values(
            address=address,
            signature=e.signature,
            slot=e.slot,
            block_time=e.timestamp,
            tx_type=e.tx_type,
            programs=e.programs,
            payload_json={"description": e.description, **e.raw},
        )
        stmt = stmt.prefix_with("IGNORE")
        await session.execute(stmt)


async def similar_analyses(
    session: AsyncSession,
    embedding: list[float],
    limit: int = 5,
    exclude_address: str | None = None,
) -> list[SimilarAnalysisItem]:
    # TiDB vector cosine distance
    emb_literal = "[" + ",".join(str(float(x)) for x in embedding) + "]"
    sql = text(
        """
        SELECT address, summary,
               VEC_COSINE_DISTANCE(embedding, CAST(:emb AS VECTOR(1536))) AS distance
        FROM wallet_analyses
        WHERE embedding IS NOT NULL
          AND (:exclude IS NULL OR address <> :exclude)
        ORDER BY distance
        LIMIT :lim
        """
    )
    result = await session.execute(
        sql,
        {"emb": emb_literal, "exclude": exclude_address, "lim": limit},
    )
    rows = result.fetchall()
    return [
        SimilarAnalysisItem(address=r.address, summary=r.summary, distance=float(r.distance))
        for r in rows
    ]


async def get_analysis_by_address(session: AsyncSession, address: str) -> WalletAnalysis | None:
    result = await session.execute(select(WalletAnalysis).where(WalletAnalysis.address == address))
    return result.scalar_one_or_none()
