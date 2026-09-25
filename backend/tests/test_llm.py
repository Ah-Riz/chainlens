from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas import AnalyzeStats, TokenBalance, WalletIntelligence
from app.services.llm import is_plausible_gemini_key, llm_summarize, rule_based_summary
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


def test_is_plausible_gemini_key() -> None:
    assert is_plausible_gemini_key("AIzaSyDummyKeyForTestsOnly123")
    assert not is_plausible_gemini_key("")
    assert not is_plausible_gemini_key("sk-not-a-gemini-key")


def _sample_events() -> list[ActivityEvent]:
    return [
        ActivityEvent(
            signature="s1",
            tx_type="SOL_TRANSFER",
            description="received 1.0000 SOL",
            programs=["System Program"],
        ),
    ]


def _llm_json() -> str:
    return json.dumps(
        {
            "summary": "This wallet swapped via Jupiter.",
            "protocol_interactions": [{"name": "Jupiter", "count": 2}],
            "notable_transfers": [
                {
                    "direction": "in",
                    "asset": "SOL",
                    "amount": "1.0",
                    "counterparty_label": "external",
                }
            ],
        }
    )


@pytest.mark.asyncio
async def test_llm_summarize_mock_when_no_key() -> None:
    with patch("app.services.llm.settings") as mock_settings:
        mock_settings.mock_analyze = False
        mock_settings.gemini_api_key = ""
        mock_settings.gemini_model = "gemini-3.8-flash"
        summary, structured, mock, model, fallback_used = await llm_summarize(
            "11111111111111111111111111111111",
            _sample_events(),
            ["System Program"],
            AnalyzeStats(tx_count=1, unique_counterparties=0, protocols=["System Program"]),
        )
    assert mock is True
    assert model is None
    assert fallback_used is False
    assert summary
    assert structured is not None


@pytest.mark.asyncio
async def test_llm_summarize_mock_when_implausible_key() -> None:
    with patch("app.services.llm.settings") as mock_settings:
        mock_settings.mock_analyze = False
        mock_settings.gemini_api_key = "sk-openai-style-key"
        mock_settings.gemini_model = "gemini-3.8-flash"
        _, _, mock, model, fallback_used = await llm_summarize(
            "11111111111111111111111111111111",
            _sample_events(),
            ["System Program"],
        )
    assert mock is True
    assert model is None
    assert fallback_used is False


@pytest.mark.asyncio
async def test_llm_summarize_happy_path() -> None:
    response = SimpleNamespace(text=_llm_json())
    generate = AsyncMock(return_value=response)
    aio_models = SimpleNamespace(generate_content=generate)
    client = MagicMock()
    client.aio = SimpleNamespace(models=aio_models)

    with (
        patch("app.services.llm.settings") as mock_settings,
        patch("app.services.llm.genai.Client", return_value=client) as client_cls,
    ):
        mock_settings.mock_analyze = False
        mock_settings.gemini_api_key = "AIzaSyDummyKeyForTestsOnly123"
        mock_settings.gemini_model = "gemini-3.8-flash"
        summary, structured, mock, model, fallback_used = await llm_summarize(
            "11111111111111111111111111111111",
            _sample_events(),
            ["Jupiter"],
            AnalyzeStats(tx_count=1, unique_counterparties=1, protocols=["Jupiter"]),
        )

    client_cls.assert_called_once_with(api_key="AIzaSyDummyKeyForTestsOnly123")
    generate.assert_awaited_once()
    assert mock is False
    assert model == "gemini-3.8-flash"
    assert fallback_used is False
    assert "Jupiter" in summary
    assert structured.protocol_interactions[0].name == "Jupiter"
    assert structured.notable_transfers[0].asset == "SOL"


class _RetryableError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


@pytest.mark.asyncio
async def test_llm_summarize_fallback_on_503() -> None:
    ok = SimpleNamespace(text=_llm_json())
    generate = AsyncMock(
        side_effect=[
            _RetryableError(503, "Service Unavailable — high demand"),
            ok,
        ]
    )
    aio_models = SimpleNamespace(generate_content=generate)
    client = MagicMock()
    client.aio = SimpleNamespace(models=aio_models)

    with (
        patch("app.services.llm.settings") as mock_settings,
        patch("app.services.llm.genai.Client", return_value=client),
    ):
        mock_settings.mock_analyze = False
        mock_settings.gemini_api_key = "AIzaSyDummyKeyForTestsOnly123"
        mock_settings.gemini_model = "gemini-3.8-flash"
        summary, _, mock, model, fallback_used = await llm_summarize(
            "11111111111111111111111111111111",
            _sample_events(),
            ["Jupiter"],
        )

    assert mock is False
    assert model == "gemini-3.7-flash"
    assert fallback_used is True
    assert "Jupiter" in summary
    assert generate.await_count == 2
    assert generate.await_args_list[0].kwargs["model"] == "gemini-3.8-flash"
    assert generate.await_args_list[1].kwargs["model"] == "gemini-3.7-flash"


@pytest.mark.asyncio
async def test_llm_summarize_fallback_on_404_new_users() -> None:
    ok = SimpleNamespace(text=_llm_json())
    generate = AsyncMock(
        side_effect=[
            _RetryableError(404, "models/gemini-3.8-flash is no longer available to new users"),
            ok,
        ]
    )
    aio_models = SimpleNamespace(generate_content=generate)
    client = MagicMock()
    client.aio = SimpleNamespace(models=aio_models)

    with (
        patch("app.services.llm.settings") as mock_settings,
        patch("app.services.llm.genai.Client", return_value=client),
    ):
        mock_settings.mock_analyze = False
        mock_settings.gemini_api_key = "AIzaSyDummyKeyForTestsOnly123"
        mock_settings.gemini_model = "gemini-3.8-flash"
        _, _, mock, model, fallback_used = await llm_summarize(
            "11111111111111111111111111111111",
            _sample_events(),
            ["Jupiter"],
        )

    assert mock is False
    assert model == "gemini-3.7-flash"
    assert fallback_used is True


@pytest.mark.asyncio
async def test_llm_summarize_non_retryable_falls_to_rule_based() -> None:
    generate = AsyncMock(side_effect=_RetryableError(401, "API key not valid"))
    aio_models = SimpleNamespace(generate_content=generate)
    client = MagicMock()
    client.aio = SimpleNamespace(models=aio_models)

    with (
        patch("app.services.llm.settings") as mock_settings,
        patch("app.services.llm.genai.Client", return_value=client),
    ):
        mock_settings.mock_analyze = False
        mock_settings.gemini_api_key = "AIzaSyDummyKeyForTestsOnly123"
        mock_settings.gemini_model = "gemini-3.8-flash"
        _, _, mock, model, fallback_used = await llm_summarize(
            "11111111111111111111111111111111",
            _sample_events(),
            ["System Program"],
        )

    assert mock is True
    assert model is None
    assert fallback_used is False
    assert generate.await_count == 1
