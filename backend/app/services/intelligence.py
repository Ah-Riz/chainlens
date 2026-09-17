"""Heuristic wallet persona + signals from already-decoded activity."""

from __future__ import annotations

from app.schemas import AnalyzeStats, TokenBalance, WalletIntelligence
from app.services.solana.decoder import ActivityEvent

# ponytail: crude thresholds; tune or replace with learned scores if noise rises
_DEX_LABELS = {"Jupiter", "Jupiter v4", "Raydium AMM", "Raydium CLMM", "Orca Whirlpool", "Orca"}
_TRANSFER_TYPES = {"SOL_TRANSFER", "SPL_TRANSFER"}


def classify_wallet(
    events: list[ActivityEvent],
    stats: AnalyzeStats,
    balances: list[TokenBalance],
) -> WalletIntelligence:
    tx_count = stats.tx_count
    type_counts: dict[str, int] = {}
    for e in events:
        type_counts[e.tx_type] = type_counts.get(e.tx_type, 0) + 1

    swap_n = type_counts.get("SWAP_HINT", 0)
    transfer_n = sum(type_counts.get(t, 0) for t in _TRANSFER_TYPES)
    swap_share = swap_n / tx_count if tx_count else 0.0
    transfer_share = transfer_n / tx_count if tx_count else 0.0
    protocols = set(stats.protocols)
    has_dex = bool(protocols & _DEX_LABELS) or swap_share >= 0.4

    label = _label(tx_count, has_dex, protocols, stats.unique_counterparties, transfer_share)
    signals = _signals(events, stats, balances, swap_share)
    return WalletIntelligence(label=label, signals=signals)


def _label(
    tx_count: int,
    has_dex: bool,
    protocols: set[str],
    counterparties: int,
    transfer_share: float,
) -> str:
    if tx_count == 0:
        return "inactive"
    if tx_count <= 2:
        return "fresh"
    if has_dex:
        return "trader"
    if "Metaplex Token Metadata" in protocols:
        return "nft"
    if "Stake Program" in protocols or "Marinade" in protocols:
        return "staker"
    if counterparties >= 8 and transfer_share >= 0.5:
        return "transfer_hub"
    return "mixed"


def _signals(
    events: list[ActivityEvent],
    stats: AnalyzeStats,
    balances: list[TokenBalance],
    swap_share: float,
) -> list[str]:
    out: list[str] = []
    tx_count = stats.tx_count

    if tx_count >= 5 and stats.unique_counterparties / max(tx_count, 1) >= 0.6:
        out.append("high_counterparty_churn")
    if swap_share >= 0.5:
        out.append("swap_heavy")

    times = [e.timestamp for e in events if e.timestamp is not None]
    if len(times) >= 5 and (max(times) - min(times)) <= 3600:
        out.append("burst_activity")

    unknown = sum(1 for b in balances if "…" in b.symbol)
    if unknown >= 5:
        out.append("many_unknown_tokens")

    return out[:3]
