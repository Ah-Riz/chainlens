from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    address: str = Field(..., min_length=32, max_length=64, description="Solana wallet address")


class ProtocolInteraction(BaseModel):
    name: str
    count: int


class NotableTransfer(BaseModel):
    direction: str
    asset: str
    amount: str
    counterparty_label: str | None = None


class AnalyzeStats(BaseModel):
    tx_count: int
    unique_counterparties: int
    protocols: list[str]


class StructuredAnalysis(BaseModel):
    protocol_interactions: list[ProtocolInteraction]
    notable_transfers: list[NotableTransfer]


class TokenBalance(BaseModel):
    mint: str
    symbol: str
    amount: str
    decimals: int = 0


class TransactionItem(BaseModel):
    signature: str
    type: str
    description: str
    timestamp: int | None = None
    programs: list[str] = Field(default_factory=list)
    slot: int | None = None


class AnalyzeResponse(BaseModel):
    address: str
    summary: str
    stats: AnalyzeStats
    balances: list[TokenBalance] = Field(default_factory=list)
    transactions: list[TransactionItem] = Field(default_factory=list)
    structured: StructuredAnalysis
    mock: bool = False


class TransactionsResponse(BaseModel):
    address: str
    transactions: list[TransactionItem]


class BalancesResponse(BaseModel):
    address: str
    balances: list[TokenBalance]


class SummaryRequest(BaseModel):
    address: str = Field(..., min_length=32, max_length=64)


class SummaryResponse(BaseModel):
    address: str
    summary: str
    structured: StructuredAnalysis
    mock: bool = False


class SimilarAnalysisItem(BaseModel):
    address: str
    summary: str
    distance: float


class SimilarAnalysesResponse(BaseModel):
    items: list[SimilarAnalysisItem]
