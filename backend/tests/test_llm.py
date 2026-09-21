from app.schemas import AnalyzeStats, TokenBalance, WalletIntelligence
from app.services.llm import rule_based_summary
from app.services.solana.decoder import ActivityEvent


def test_rule_based_mentions_label_and_amounts() -> None:
    events = [
        ActivityEvent(
            signature="s1",
            tx_type="SOL_TRANSFER",
            description="received 1.0000 SOL",
            programs=["System Program"],
        ),
        ActivityEvent(
            signature="s2",
            tx_type="SWAP_HINT",
            description="Likely swap via Jupiter",
            programs=["Jupiter", "SPL Token"],
        ),
    ]
    stats = AnalyzeStats(tx_count=2, unique_counterparties=1, protocols=["Jupiter", "System Program"])
    intel = WalletIntelligence(label="trader", signals=["swap_heavy"])
    balances = [TokenBalance(mint="So1111", symbol="SOL", amount="2.5", decimals=9)]

    summary, structured = rule_based_summary(
        "11111111111111111111111111111111",
        events,
        stats.protocols,
        stats,
        balances,
        intel,
    )

    assert "trader" in summary
    assert "swap heavy" in summary
    assert "2.5 SOL" in summary
    assert structured.protocol_interactions[0].count >= 1
    assert any(t.amount == "1.0000" and t.asset == "SOL" for t in structured.notable_transfers)
