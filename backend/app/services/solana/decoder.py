from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.solana.programs import DEX_PROGRAMS, label_program, mint_symbol


@dataclass
class ActivityEvent:
    signature: str
    tx_type: str
    description: str
    timestamp: int | None = None
    slot: int | None = None
    programs: list[str] = field(default_factory=list)
    counterparties: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


def _collect_instructions(tx: dict[str, Any]) -> list[dict[str, Any]]:
    message = (tx.get("transaction") or {}).get("message") or {}
    outer = list(message.get("instructions") or [])
    meta = tx.get("meta") or {}
    for inner_group in meta.get("innerInstructions") or []:
        outer.extend(inner_group.get("instructions") or [])
    return outer


def _program_id(ix: dict[str, Any]) -> str | None:
    return ix.get("programId") or ix.get("programIdIndex")


def decode_transaction(
    signature: str,
    tx: dict[str, Any] | None,
    wallet: str,
) -> ActivityEvent:
    if not tx:
        return ActivityEvent(
            signature=signature,
            tx_type="UNKNOWN",
            description="Transaction data unavailable",
        )

    block_time = tx.get("blockTime")
    slot = tx.get("slot")
    instructions = _collect_instructions(tx)
    program_ids: list[str] = []
    labels: list[str] = []
    counterparties: set[str] = set()
    spl_notes: list[str] = []
    sol_notes: list[str] = []
    has_dex = False

    for ix in instructions:
        pid = _program_id(ix)
        if not isinstance(pid, str):
            continue
        program_ids.append(pid)
        labels.append(label_program(pid))
        if pid in DEX_PROGRAMS:
            has_dex = True

        parsed = ix.get("parsed")
        if not isinstance(parsed, dict):
            continue
        info = parsed.get("info") or {}
        itype = parsed.get("type")

        if itype == "transfer" and ix.get("program") == "system":
            src = info.get("source")
            dst = info.get("destination")
            lamports = int(info.get("lamports") or 0)
            sol = lamports / 1e9
            if src == wallet:
                sol_notes.append(f"sent {sol:.4f} SOL")
                if dst:
                    counterparties.add(dst)
            elif dst == wallet:
                sol_notes.append(f"received {sol:.4f} SOL")
                if src:
                    counterparties.add(src)

        if itype in {"transfer", "transferChecked"} and ix.get("program") == "spl-token":
            mint = info.get("mint") or ""
            amount_raw = info.get("tokenAmount", {}).get("uiAmountString") or info.get("amount")
            symbol, _ = mint_symbol(mint) if mint else ("TOKEN", 0)
            src = info.get("source") or info.get("authority")
            dst = info.get("destination")
            direction = "moved"
            if src and wallet in (src, info.get("authority")):
                direction = "sent"
            if dst and wallet in str(dst):
                direction = "received"
            # Token account ownership is opaque without ATA lookup — keep generic.
            spl_notes.append(f"{direction} {amount_raw or '?'} {symbol}")
            for party in (src, dst):
                if party and party != wallet:
                    counterparties.add(str(party))

    # Prefer specific classification
    if has_dex:
        tx_type = "SWAP_HINT"
        dex_names = sorted({label_program(p) for p in program_ids if p in DEX_PROGRAMS})
        description = f"Likely swap via {', '.join(dex_names)}"
        if spl_notes:
            description += f" ({'; '.join(spl_notes[:3])})"
    elif spl_notes:
        tx_type = "SPL_TRANSFER"
        description = "; ".join(spl_notes[:3])
    elif sol_notes:
        tx_type = "SOL_TRANSFER"
        description = "; ".join(sol_notes[:3])
    elif labels:
        tx_type = "PROGRAM_INTERACTION"
        unique_labels = list(dict.fromkeys(labels))
        description = f"Interacted with {', '.join(unique_labels[:4])}"
    else:
        tx_type = "UNKNOWN"
        description = "Unrecognized activity"

    return ActivityEvent(
        signature=signature,
        tx_type=tx_type,
        description=description,
        timestamp=block_time,
        slot=slot,
        programs=list(dict.fromkeys(labels)),
        counterparties=list(counterparties),
        raw={"program_ids": list(dict.fromkeys(program_ids))},
    )


def decode_many(
    pairs: list[tuple[str, dict[str, Any] | None]],
    wallet: str,
) -> list[ActivityEvent]:
    return [decode_transaction(sig, tx, wallet) for sig, tx in pairs]
