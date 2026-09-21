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


def test_rule_based_program_not_wallet() -> None:
    events = [
        ActivityEvent(signature="s1", tx_type="SWAP_HINT", description="Likely swap via Jupiter", programs=["Jupiter"]),
    ]
    stats = AnalyzeStats(tx_count=1, unique_counterparties=0, protocols=["Jupiter"])
    intel = WalletIntelligence(label="program", signals=[])
    summary, _ = rule_based_summary(
        "KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD",
        events,
        stats.protocols,
        stats,
        [],
        intel,
        account_kind="program",
        owner_label="KLend",
        what_is_this="This is a program (on-chain code / smart contract) — KLend. It is not a personal wallet.",
    )
    assert "program" in summary.lower()
    assert "trader" not in summary.lower()
    assert "This wallet" not in summary
