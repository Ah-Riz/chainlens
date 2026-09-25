from __future__ import annotations

import logging

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.schemas import (
    AnalyzeResponse,
    AnalyzeStats,
    TokenBalance,
    TransactionItem,
)
from app.services.address import is_valid_solana_address
from app.services.cache import upsert_analysis
from app.services.intelligence import classify_wallet
from app.services.llm import llm_summarize, rule_based_summary
from app.services.solana import SolanaRpc, decode_transaction, fetch_balances
from app.services.solana.account_kind import (
    AccountClassification,
    classify_with_address_label,
    what_is_this_for,
)
from app.services.solana.decoder import ActivityEvent

logger = logging.getLogger(__name__)


async def _persist_analysis(
    session: AsyncSession,
    address: str,
    summary: str,
    stats: AnalyzeStats,
    structured,
) -> None:
    """Best-effort TiDB write — Analyze UX must not depend on DB availability."""
    try:
        await upsert_analysis(
            session,
            address,
            summary,
            stats.model_dump(),
            structured.model_dump(),
        )
        await session.commit()
    except Exception:
        logger.exception("Failed to persist analysis for %s", address)
        try:
            await session.rollback()
        except Exception:
            logger.exception("Rollback failed after persist error for %s", address)


def _require_address(address: str) -> str:
    if not is_valid_solana_address(address):
        raise HTTPException(status_code=400, detail="Invalid Solana address")
    return address.strip()


def _events_to_items(events: list[ActivityEvent]) -> list[TransactionItem]:
    return [
        TransactionItem(
            signature=e.signature,
            type=e.tx_type,
            description=e.description,
            timestamp=e.timestamp,
            programs=e.programs,
            slot=e.slot,
        )
        for e in events
    ]


def _stats(events: list[ActivityEvent]) -> AnalyzeStats:
    counterparties: set[str] = set()
    protocols: list[str] = []
    seen: set[str] = set()
    for e in events:
        counterparties.update(e.counterparties)
        for p in e.programs:
            if p not in seen and not p.endswith("…"):
                seen.add(p)
                protocols.append(p)
    return AnalyzeStats(
        tx_count=len(events),
        unique_counterparties=len(counterparties),
        protocols=protocols[:12],
    )


async def fetch_activity(address: str, rpc: SolanaRpc | None = None) -> list[ActivityEvent]:
    client = rpc or SolanaRpc()
    sigs = await client.get_signatures_for_address(address, settings.tx_fetch_limit)
    events: list[ActivityEvent] = []
    for entry in sigs:
        signature = entry.get("signature")
        if not signature:
            continue
        tx = await client.get_transaction(signature)
        events.append(decode_transaction(signature, tx, address))
    return events


async def _classify_address(address: str, rpc: SolanaRpc) -> AccountClassification:
    try:
        info = await rpc.get_account_info(address)
    except Exception:
        logger.exception("getAccountInfo failed for %s", address)
        return AccountClassification(
            kind="wallet",
            owner_program=None,
            owner_label=None,
            what_is_this=what_is_this_for("wallet", None),
        )
    return classify_with_address_label(info, address)


def _mock_response(address: str) -> AnalyzeResponse:
    # ≥3 txs + DEX so classify_wallet → trader / swap_heavy
    events = [
        ActivityEvent(
            signature=f"MockSig{i:064d}",
            tx_type="SWAP_HINT",
            description="Likely swap via Jupiter",
            timestamp=1700000000 - i,
            programs=["Jupiter", "SPL Token"],
            counterparties=[f"Counter{i:043d}"],
        )
        for i in range(1, 4)
    ] + [
        ActivityEvent(
            signature="MockSig0000000000000000000000000000000000000000000000000000000099",
            tx_type="SOL_TRANSFER",
            description="received 1.0000 SOL",
            timestamp=1699990000,
            programs=["System Program"],
            counterparties=["Counter2222222222222222222222222222222222222"],
        ),
    ]
    balances = [
        TokenBalance(
            mint="So11111111111111111111111111111111111111112",
            symbol="SOL",
            amount="2.5",
            decimals=9,
        ),
        TokenBalance(
            mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            symbol="USDC",
            amount="150.00",
            decimals=6,
        ),
    ]
    stats = _stats(events)
    what = what_is_this_for("wallet", None)
    intelligence = classify_wallet(events, stats, balances, "wallet")
    summary, structured = rule_based_summary(
        address,
        events,
        stats.protocols,
        stats,
        balances,
        intelligence,
        account_kind="wallet",
        what_is_this=what,
    )
    summary = (
        f"{summary}\n"
        "(Mock — set MOCK_ANALYZE=false and configure SOLANA_RPC_URL + GEMINI_API_KEY.)"
    )
    return AnalyzeResponse(
        address=address,
        summary=summary,
        stats=stats,
        balances=balances,
        transactions=_events_to_items(events),
        structured=structured,
        intelligence=intelligence,
        account_kind="wallet",
        owner_program="11111111111111111111111111111111",
        owner_label="System Program",
        what_is_this=what,
        mock=True,
        model=None,
        fallback_used=False,
    )


async def analyze_wallet(address: str, session: AsyncSession | None = None) -> AnalyzeResponse:
    normalized = _require_address(address)

    if settings.mock_analyze:
        return _mock_response(normalized)

    rpc = SolanaRpc()
    acct = await _classify_address(normalized, rpc)
    events = await fetch_activity(normalized, rpc)
    balances = await fetch_balances(normalized, rpc)
    stats = _stats(events)
    intelligence = classify_wallet(events, stats, balances, acct.kind)
    summary, structured, mock, model, fallback_used = await llm_summarize(
        normalized,
        events,
        stats.protocols,
        stats,
        balances,
        intelligence,
        account_kind=acct.kind,
        owner_label=acct.owner_label,
        what_is_this=acct.what_is_this,
    )

    if session is not None:
        await _persist_analysis(session, normalized, summary, stats, structured)

    return AnalyzeResponse(
        address=normalized,
        summary=summary,
        stats=stats,
        balances=balances,
        transactions=_events_to_items(events),
        structured=structured,
        intelligence=intelligence,
        account_kind=acct.kind,
        owner_program=acct.owner_program,
        owner_label=acct.owner_label,
        what_is_this=acct.what_is_this,
        mock=mock,
        model=model,
        fallback_used=fallback_used,
    )
