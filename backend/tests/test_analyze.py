import os
from unittest.mock import AsyncMock, MagicMock, patch

os.environ["MOCK_ANALYZE"] = "true"

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)

# Valid 32-byte pubkey (System Program)
ADDRESS = "11111111111111111111111111111111"


def test_health() -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["chain"] == "solana"


def test_analyze_mock() -> None:
    settings.mock_analyze = True
    res = client.post("/analyze", json={"address": ADDRESS})
    assert res.status_code == 200
    body = res.json()
    assert body["mock"] is True
    assert body["address"] == ADDRESS
    assert "summary" in body
    assert "trader" in body["summary"].lower() or body["intelligence"]["label"] == "trader"
    assert len(body["transactions"]) >= 1
    assert len(body["structured"]["notable_transfers"]) >= 1
    assert body["account_kind"] == "wallet"
    assert "wallet" in body["what_is_this"].lower()
    assert body["intelligence"]["label"] == "trader"
    assert "swap_heavy" in body["intelligence"]["signals"]


def test_analyze_invalid() -> None:
    # Long enough for schema; fails Solana base58/32-byte check → 400
    res = client.post("/analyze", json={"address": "0x" + "ab" * 20})
    assert res.status_code == 400


def test_analyze_empty_wallet() -> None:
    settings.mock_analyze = False
    settings.gemini_api_key = ""

    rpc = MagicMock()
    rpc.get_signatures_for_address = AsyncMock(return_value=[])
    rpc.get_account_info = AsyncMock(return_value=None)
    rpc.get_balance = AsyncMock(return_value=0)
    rpc.get_token_accounts_by_owner = AsyncMock(return_value=[])

    with (
        patch("app.services.analyze.SolanaRpc", return_value=rpc),
        patch("app.services.analyze._persist_analysis", new_callable=AsyncMock),
    ):
        res = client.post("/analyze", json={"address": ADDRESS})

    assert res.status_code == 200
    body = res.json()
    assert body["transactions"] == []
    assert body["stats"]["tx_count"] == 0
    assert body["mock"] is True


def test_analyze_rpc_failure_502() -> None:
    settings.mock_analyze = False

    rpc = MagicMock()
    rpc.get_account_info = AsyncMock(return_value=None)
    rpc.get_signatures_for_address = AsyncMock(
        side_effect=HTTPException(status_code=502, detail="Solana RPC error: boom")
    )

    with patch("app.services.analyze.SolanaRpc", return_value=rpc):
        res = client.post("/analyze", json={"address": ADDRESS})

    assert res.status_code == 502
    assert "Solana RPC" in res.json()["detail"]
