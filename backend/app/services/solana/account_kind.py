"""Classify any Solana pubkey: wallet, program, mint, ATA, or protocol account."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.solana.programs import label_program

SYSTEM_PROGRAM = "11111111111111111111111111111111"
TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
TOKEN_2022_PROGRAM = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
_TOKEN_OWNERS = {TOKEN_PROGRAM, TOKEN_2022_PROGRAM}


@dataclass(frozen=True)
class AccountClassification:
    kind: str
    owner_program: str | None
    owner_label: str | None
    what_is_this: str


def _parsed_type(info: dict[str, Any]) -> str | None:
    data = info.get("data")
    if isinstance(data, dict):
        parsed = data.get("parsed")
        if isinstance(parsed, dict):
            t = parsed.get("type")
            return str(t) if t else None
    return None


def what_is_this_for(kind: str, owner_label: str | None) -> str:
    if kind == "program":
        if owner_label and not owner_label.endswith("…"):
            return (
                f"This is a program (on-chain code / smart contract) — {owner_label}. "
                "It is not a personal wallet."
            )
        return "This is a program (on-chain code / smart contract), not a personal wallet."
    if kind == "token_mint":
        return "This is a token mint (the token’s definition on-chain), not a wallet."
    if kind == "token_account":
        return (
            "This is a token account holding one token for a wallet — "
            "not the wallet address itself."
        )
    if kind == "protocol_account":
        owned = owner_label or "a program"
        return (
            f"This is a protocol account (vault, market, or PDA) owned by {owned}. "
            "It is not a personal wallet."
        )
    if kind == "unknown":
        return "No on-chain account found for this address (unused or closed)."
    return "This looks like a wallet (user account)."


def classify_account(info: dict[str, Any] | None) -> AccountClassification:
    """Map getAccountInfo value (or None) to a newbie-safe kind."""
    if not info:
        return AccountClassification(
            kind="unknown",
            owner_program=None,
            owner_label=None,
            what_is_this=what_is_this_for("unknown", None),
        )

    owner = info.get("owner")
    owner_str = str(owner) if owner else None
    owner_label = label_program(owner_str) if owner_str else None

    if info.get("executable"):
        return AccountClassification(
            kind="program",
            owner_program=owner_str,
            owner_label=None,
            what_is_this=what_is_this_for("program", None),
        )

    if owner_str in _TOKEN_OWNERS:
        ptype = _parsed_type(info)
        kind = "token_mint" if ptype == "mint" else "token_account"
        return AccountClassification(
            kind=kind,
            owner_program=owner_str,
            owner_label=owner_label,
            what_is_this=what_is_this_for(kind, owner_label),
        )

    if owner_str == SYSTEM_PROGRAM or owner_str is None:
        return AccountClassification(
            kind="wallet",
            owner_program=owner_str,
            owner_label=owner_label,
            what_is_this=what_is_this_for("wallet", owner_label),
        )

    return AccountClassification(
        kind="protocol_account",
        owner_program=owner_str,
        owner_label=owner_label,
        what_is_this=what_is_this_for("protocol_account", owner_label),
    )


def classify_with_address_label(
    info: dict[str, Any] | None,
    address: str,
) -> AccountClassification:
    """Like classify_account, but for programs use the address's known program label."""
    base = classify_account(info)
    if base.kind != "program":
        return base
    addr_label = label_program(address)
    nice = None if addr_label.endswith("…") else addr_label
    return AccountClassification(
        kind="program",
        owner_program=base.owner_program,
        owner_label=nice,
        what_is_this=what_is_this_for("program", nice),
    )
