from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.analyze import analyze_wallet

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    body: AnalyzeRequest,
    session: AsyncSession = Depends(get_session),
) -> AnalyzeResponse:
    return await analyze_wallet(body.address, session)
