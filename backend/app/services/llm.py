from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from app.config import settings
from app.schemas import NotableTransfer, ProtocolInteraction, StructuredAnalysis
from app.services.solana.decoder import ActivityEvent


def rule_based_summary(
    address: str,
    events: list[ActivityEvent],
    protocols: list[str],
) -> tuple[str, StructuredAnalysis]:
    tx_count = len(events)
    type_counts: dict[str, int] = {}
    for e in events:
        type_counts[e.tx_type] = type_counts.get(e.tx_type, 0) + 1

    parts = [f"Wallet {address[:4]}…{address[-4:]} has {tx_count} recent transactions."]
    if protocols:
        parts.append(f"Observed programs: {', '.join(protocols[:6])}.")
    if type_counts.get("SWAP_HINT"):
        parts.append(f"About {type_counts['SWAP_HINT']} look like DEX swaps.")
    if type_counts.get("SPL_TRANSFER"):
        parts.append(f"{type_counts['SPL_TRANSFER']} SPL token transfers.")
    if type_counts.get("SOL_TRANSFER"):
        parts.append(f"{type_counts['SOL_TRANSFER']} native SOL transfers.")
    if tx_count == 0:
        parts = [f"Wallet {address[:4]}…{address[-4:]} has no recent transactions in the fetched window."]

    interactions = [ProtocolInteraction(name=p, count=1) for p in protocols[:8]]
    transfers: list[NotableTransfer] = []
    for e in events[:5]:
        if e.tx_type in {"SOL_TRANSFER", "SPL_TRANSFER", "SWAP_HINT"}:
            transfers.append(
                NotableTransfer(
                    direction="activity",
                    asset=e.tx_type,
                    amount="n/a",
                    counterparty_label=e.description[:80],
                )
            )

    structured = StructuredAnalysis(
        protocol_interactions=interactions,
        notable_transfers=transfers,
    )
    return " ".join(parts), structured


async def llm_summarize(
    address: str,
    events: list[ActivityEvent],
    protocols: list[str],
) -> tuple[str, StructuredAnalysis, bool]:
    """Return summary, structured, mock_flag."""
    if settings.mock_analyze or not settings.openai_api_key:
        summary, structured = rule_based_summary(address, events, protocols)
        return summary, structured, True

    compact = [
        {
            "type": e.tx_type,
            "description": e.description,
            "programs": e.programs[:4],
            "timestamp": e.timestamp,
        }
        for e in events[:30]
    ]
    system = (
        "You are ChainLens, a Solana wallet analyst. "
        "Explain wallet activity in clear English for crypto users. "
        "Respond with JSON only matching the schema."
    )
    user = json.dumps(
        {
            "address": address,
            "protocols": protocols,
            "events": compact,
            "schema": {
                "summary": "string paragraph",
                "protocol_interactions": [{"name": "str", "count": "int"}],
                "notable_transfers": [
                    {
                        "direction": "in|out|activity",
                        "asset": "str",
                        "amount": "str",
                        "counterparty_label": "str|null",
                    }
                ],
            },
        }
    )

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    try:
        res = await client.chat.completions.create(
            model=settings.llm_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        raw = res.choices[0].message.content or "{}"
        data: dict[str, Any] = json.loads(raw)
    except Exception:
        summary, structured = rule_based_summary(address, events, protocols)
        return summary, structured, True

    interactions = [
        ProtocolInteraction(name=str(i.get("name", "Unknown")), count=int(i.get("count", 1)))
        for i in (data.get("protocol_interactions") or [])
        if isinstance(i, dict)
    ]
    transfers = [
        NotableTransfer(
            direction=str(t.get("direction", "activity")),
            asset=str(t.get("asset", "?")),
            amount=str(t.get("amount", "?")),
            counterparty_label=t.get("counterparty_label"),
        )
        for t in (data.get("notable_transfers") or [])
        if isinstance(t, dict)
    ]
    summary = str(data.get("summary") or "").strip() or rule_based_summary(address, events, protocols)[0]
    return summary, StructuredAnalysis(protocol_interactions=interactions, notable_transfers=transfers), False
