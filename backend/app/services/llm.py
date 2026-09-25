from __future__ import annotations

import json
import logging
import re
from typing import Any

from google import genai
from google.genai import types

from app.config import settings
from app.schemas import (
    AnalyzeStats,
    NotableTransfer,
    ProtocolInteraction,
    StructuredAnalysis,
    TokenBalance,
    WalletIntelligence,
)
from app.services.solana.decoder import ActivityEvent

logger = logging.getLogger(__name__)

_AMOUNT_RE = re.compile(
    r"(sent|received|transferred)\s+([\d.]+)\s+(\w+)",
    re.IGNORECASE,
)

DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"

# Never include gemini-2.5-* or gemini-2.0-* (often 404 for new users).
_FALLBACK_MODELS = (
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
)


def is_plausible_gemini_key(key: str) -> bool:
    """Google AI Studio keys usually start with AIza."""
    return bool(key) and key.startswith("AIza")


def _protocol_counts(events: list[ActivityEvent], protocols: list[str]) -> list[ProtocolInteraction]:
    counts: dict[str, int] = {}
    for e in events:
        for p in e.programs:
            if p.endswith("…"):
                continue
            counts[p] = counts.get(p, 0) + 1
    ordered = [p for p in protocols if p in counts] + [p for p in counts if p not in protocols]
    return [ProtocolInteraction(name=p, count=counts[p]) for p in ordered[:8]]


def _notable_from_events(events: list[ActivityEvent]) -> list[NotableTransfer]:
    transfers: list[NotableTransfer] = []
    for e in events:
        if e.tx_type not in {"SOL_TRANSFER", "SPL_TRANSFER", "SWAP_HINT"}:
            continue
        desc = e.description or ""
        m = _AMOUNT_RE.search(desc)
        if m:
            verb, amount, asset = m.group(1).lower(), m.group(2), m.group(3)
            direction = "out" if verb == "sent" else "in" if verb == "received" else "activity"
            transfers.append(
                NotableTransfer(
                    direction=direction,
                    asset=asset,
                    amount=amount,
                    counterparty_label=desc[:80],
                )
            )
        else:
            transfers.append(
                NotableTransfer(
                    direction="activity",
                    asset=e.tx_type,
                    amount=desc[:40] if desc else "n/a",
                    counterparty_label=desc[:80] or None,
                )
            )
        if len(transfers) >= 5:
            break
    return transfers


def rule_based_summary(
    address: str,
    events: list[ActivityEvent],
    protocols: list[str],
    stats: AnalyzeStats | None = None,
    balances: list[TokenBalance] | None = None,
    intelligence: WalletIntelligence | None = None,
    account_kind: str = "wallet",
    owner_label: str | None = None,
    what_is_this: str | None = None,
) -> tuple[str, StructuredAnalysis]:
    tx_count = stats.tx_count if stats else len(events)
    counterparties = stats.unique_counterparties if stats else 0
    type_counts: dict[str, int] = {}
    for e in events:
        type_counts[e.tx_type] = type_counts.get(e.tx_type, 0) + 1

    short = f"{address[:4]}…{address[-4:]}"
    intro = what_is_this or "This looks like a wallet (user account)."
    parts: list[str] = [intro]

    if account_kind != "wallet":
        noun = {
            "program": "program",
            "token_mint": "token mint",
            "token_account": "token account",
            "protocol_account": "protocol account",
            "unknown": "address",
        }.get(account_kind, "address")
        if tx_count == 0:
            parts.append(f"No recent transactions mentioning this {noun} ({short}).")
        else:
            parts.append(
                f"Recent activity involving this {noun} ({short}): "
                f"{tx_count} txs across {counterparties} counterparties."
            )
            if owner_label and account_kind == "protocol_account":
                parts.append(f"Owner program: {owner_label}.")
            if protocols:
                parts.append(f"Programs seen in those txs: {', '.join(protocols[:6])}.")
            if type_counts.get("SWAP_HINT"):
                parts.append(f"About {type_counts['SWAP_HINT']} look like DEX swaps.")
            if type_counts.get("SPL_TRANSFER"):
                parts.append(f"{type_counts['SPL_TRANSFER']} SPL token transfers.")
            if type_counts.get("SOL_TRANSFER"):
                parts.append(f"{type_counts['SOL_TRANSFER']} native SOL transfers.")
            if intelligence and intelligence.signals:
                parts.append(
                    f"Signals: {', '.join(s.replace('_', ' ') for s in intelligence.signals)}."
                )
    elif tx_count == 0:
        parts.append(f"Address {short} looks inactive in the fetched window — no recent transactions.")
    else:
        label = intelligence.label if intelligence else "mixed"
        parts.append(
            f"This wallet ({short}) reads as a {label} "
            f"with {tx_count} recent txs across {counterparties} counterparties."
        )
        if intelligence and intelligence.signals:
            parts.append(f"Signals: {', '.join(s.replace('_', ' ') for s in intelligence.signals)}.")
        if balances:
            top = ", ".join(f"{b.amount} {b.symbol}" for b in balances[:5])
            parts.append(f"Holdings include {top}.")
        if protocols:
            parts.append(f"Most active programs: {', '.join(protocols[:6])}.")
        if type_counts.get("SWAP_HINT"):
            parts.append(f"About {type_counts['SWAP_HINT']} look like DEX swaps.")
        if type_counts.get("SPL_TRANSFER"):
            parts.append(f"{type_counts['SPL_TRANSFER']} SPL token transfers.")
        if type_counts.get("SOL_TRANSFER"):
            parts.append(f"{type_counts['SOL_TRANSFER']} native SOL transfers.")

    structured = StructuredAnalysis(
        protocol_interactions=_protocol_counts(events, protocols),
        notable_transfers=_notable_from_events(events),
    )
    return "\n".join(parts), structured


def _analyst_brief(
    address: str,
    events: list[ActivityEvent],
    protocols: list[str],
    stats: AnalyzeStats | None,
    balances: list[TokenBalance] | None,
    intelligence: WalletIntelligence | None,
    account_kind: str,
    owner_label: str | None,
    what_is_this: str | None,
) -> dict[str, Any]:
    return {
        "address": address,
        "account_kind": account_kind,
        "owner_label": owner_label,
        "what_is_this": what_is_this,
        "intelligence": {
            "label": intelligence.label if intelligence else None,
            "signals": list(intelligence.signals) if intelligence else [],
        },
        "stats": {
            "tx_count": stats.tx_count if stats else len(events),
            "unique_counterparties": stats.unique_counterparties if stats else 0,
            "protocols": protocols,
        },
        "balances": [
            {"symbol": b.symbol, "amount": b.amount, "mint": b.mint[:8] + "…"}
            for b in (balances or [])[:5]
        ],
        "events": [
            {
                "type": e.tx_type,
                "description": e.description,
                "programs": e.programs[:4],
                "counterparties": [c[:8] + "…" for c in e.counterparties[:3]],
                "timestamp": e.timestamp,
            }
            for e in events[:30]
        ],
    }


def _models_to_try(primary: str) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for m in (primary, *_FALLBACK_MODELS):
        if m and m not in seen:
            seen.add(m)
            ordered.append(m)
    return ordered


def _exception_status_and_text(exc: BaseException) -> tuple[int | None, str]:
    status: int | None = None
    for attr in ("status_code", "code"):
        raw = getattr(exc, attr, None)
        if isinstance(raw, int):
            status = raw
            break
    parts = [str(exc)]
    resp = getattr(exc, "response", None)
    if resp is not None:
        resp_status = getattr(resp, "status_code", None)
        if isinstance(resp_status, int):
            status = resp_status
        parts.append(str(getattr(resp, "text", "") or ""))
    msg = getattr(exc, "message", None)
    if msg:
        parts.append(str(msg))
    return status, " ".join(parts)


def _is_retryable_model_error(exc: BaseException) -> bool:
    """Retry on capacity / unavailable / new-user 404; not on auth or other hard failures."""
    status, text = _exception_status_and_text(exc)
    lower = text.lower()
    if status in (429, 503):
        return True
    if "unavailable" in lower or "high demand" in lower or "resource_exhausted" in lower:
        return True
    if status == 404 and "no longer available to new users" in lower:
        return True
    if "no longer available to new users" in lower:
        return True
    return False


def _parse_llm_json(raw: str) -> dict[str, Any]:
    data = json.loads(raw or "{}")
    if not isinstance(data, dict):
        raise ValueError("LLM JSON root must be an object")
    return data


async def llm_summarize(
    address: str,
    events: list[ActivityEvent],
    protocols: list[str],
    stats: AnalyzeStats | None = None,
    balances: list[TokenBalance] | None = None,
    intelligence: WalletIntelligence | None = None,
    account_kind: str = "wallet",
    owner_label: str | None = None,
    what_is_this: str | None = None,
) -> tuple[str, StructuredAnalysis, bool, str | None, bool]:
    """Return summary, structured, mock_flag, model, fallback_used."""
    kwargs = dict(
        stats=stats,
        balances=balances,
        intelligence=intelligence,
        account_kind=account_kind,
        owner_label=owner_label,
        what_is_this=what_is_this,
    )
    if settings.mock_analyze or not is_plausible_gemini_key(settings.gemini_api_key):
        summary, structured = rule_based_summary(address, events, protocols, **kwargs)
        return summary, structured, True, None, False

    system = (
        "You are ChainLens, a Solana address analyst for newcomers and crypto users. "
        "Always respect account_kind and what_is_this from the brief. "
        "If account_kind is not wallet, NEVER call it a wallet or a trader — "
        "describe it as a program, mint, token account, or protocol account as appropriate. "
        "Lead with what the address is, then cite 2–3 concrete behaviors from the brief only — never invent. "
        "You may use short line breaks in summary for scannability. "
        "Respond with JSON only matching the schema."
    )
    user = json.dumps(
        {
            "brief": _analyst_brief(
                address,
                events,
                protocols,
                stats,
                balances,
                intelligence,
                account_kind,
                owner_label,
                what_is_this,
            ),
            "schema": {
                "summary": "string (1 short para + optional line breaks)",
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
    contents = f"{system}\n\n{user}"

    primary = (settings.gemini_model or DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
    models = _models_to_try(primary)
    client = genai.Client(api_key=settings.gemini_api_key)
    config = types.GenerateContentConfig(
        temperature=0.2,
        response_mime_type="application/json",
    )

    last_exc: BaseException | None = None
    for model in models:
        try:
            res = await client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
            raw = res.text or "{}"
            data = _parse_llm_json(raw)
        except Exception as exc:
            last_exc = exc
            if _is_retryable_model_error(exc):
                logger.warning("Gemini model %s unavailable (%s); trying next", model, exc)
                continue
            logger.exception("Gemini generate_content failed for %s", model)
            summary, structured = rule_based_summary(address, events, protocols, **kwargs)
            return summary, structured, True, None, False
        else:
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
            summary = str(data.get("summary") or "").strip() or rule_based_summary(
                address, events, protocols, **kwargs
            )[0]
            fallback_used = model != primary
            return (
                summary,
                StructuredAnalysis(protocol_interactions=interactions, notable_transfers=transfers),
                False,
                model,
                fallback_used,
            )

    if last_exc is not None:
        logger.warning("All Gemini models failed; last error: %s", last_exc)
    summary, structured = rule_based_summary(address, events, protocols, **kwargs)
    return summary, structured, True, None, False
