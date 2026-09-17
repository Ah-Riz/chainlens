from app.schemas import AnalyzeStats, TokenBalance
from app.services.intelligence import classify_wallet
from app.services.solana.decoder import ActivityEvent


def test_inactive() -> None:
    stats = AnalyzeStats(tx_count=0, unique_counterparties=0, protocols=[])
    intel = classify_wallet([], stats, [])
    assert intel.label == "inactive"
    assert intel.signals == []


def test_trader_swap_heavy() -> None:
    events = [
        ActivityEvent(signature=f"s{i}", tx_type="SWAP_HINT", description="swap", timestamp=1_700_000_000 + i)
        for i in range(6)
    ]
    stats = AnalyzeStats(tx_count=6, unique_counterparties=2, protocols=["Jupiter"])
    intel = classify_wallet(events, stats, [])
    assert intel.label == "trader"
    assert "swap_heavy" in intel.signals


def test_fresh() -> None:
    events = [ActivityEvent(signature="s1", tx_type="SOL_TRANSFER", description="sent")]
    stats = AnalyzeStats(tx_count=1, unique_counterparties=1, protocols=["System Program"])
    intel = classify_wallet(events, stats, [TokenBalance(mint="x", symbol="SOL", amount="1")])
    assert intel.label == "fresh"
