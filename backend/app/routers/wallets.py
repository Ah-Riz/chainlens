from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    BalancesResponse,
    SimilarAnalysesResponse,
    SummaryResponse,
    TransactionsResponse,
)
from app.services.address import is_valid_solana_address, normalize_address
from app.services.analyze import analyze_wallet, get_balances, get_transactions, summarize_wallet
from app.services.cache import get_analysis_by_address, similar_analyses
from app.services.embeddings import embed_text
from fastapi import HTTPException

router = APIRouter()


@router.get("/wallets/{address}/transactions", response_model=TransactionsResponse)
async def wallet_transactions(address: str) -> TransactionsResponse:
    return await get_transactions(address)


@router.get("/wallets/{address}/balances", response_model=BalancesResponse)
async def wallet_balances(address: str) -> BalancesResponse:
    return await get_balances(address)


@router.post("/wallets/{address}/summary", response_model=SummaryResponse)
async def wallet_summary(
    address: str,
    session: AsyncSession = Depends(get_session),
) -> SummaryResponse:
    return await summarize_wallet(address, session)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    body: AnalyzeRequest,
    session: AsyncSession = Depends(get_session),
) -> AnalyzeResponse:
    return await analyze_wallet(body.address, session)


@router.get("/analyses/similar", response_model=SimilarAnalysesResponse)
async def analyses_similar(
    q: str | None = None,
    address: str | None = None,
    limit: int = 5,
    session: AsyncSession = Depends(get_session),
) -> SimilarAnalysesResponse:
    embedding: list[float] | None = None
    exclude: str | None = None

    if address:
        if not is_valid_solana_address(address):
            raise HTTPException(status_code=400, detail="Invalid Solana address")
        exclude = normalize_address(address)
        row = await get_analysis_by_address(session, exclude)
        if row is not None and row.embedding is not None:
            embedding = list(row.embedding)
        elif q is None:
            raise HTTPException(status_code=404, detail="No stored analysis embedding for address")

    if embedding is None:
        if not q:
            raise HTTPException(status_code=400, detail="Provide q= or address= with stored embedding")
        embedding = await embed_text(q)
        if embedding is None:
            raise HTTPException(
                status_code=503,
                detail="Embeddings unavailable (set GEMINI_API_KEY and MOCK_ANALYZE=false)",
            )

    items = await similar_analyses(session, embedding, limit=min(limit, 20), exclude_address=exclude)
    return SimilarAnalysesResponse(items=items)
