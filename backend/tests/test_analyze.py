import os

os.environ["MOCK_ANALYZE"] = "true"

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Valid 32-byte pubkey (System Program)
ADDRESS = "11111111111111111111111111111111"


def test_health() -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["chain"] == "solana"


def test_analyze_mock() -> None:
    res = client.post("/analyze", json={"address": ADDRESS})
    assert res.status_code == 200
    body = res.json()
    assert body["mock"] is True
    assert body["address"] == ADDRESS
    assert "summary" in body
    assert len(body["transactions"]) >= 1


def test_analyze_invalid() -> None:
    # Long enough for schema; fails Solana base58/32-byte check → 400
    res = client.post("/analyze", json={"address": "0x" + "ab" * 20})
    assert res.status_code == 400


def test_transactions_mock() -> None:
    res = client.get(f"/wallets/{ADDRESS}/transactions")
    assert res.status_code == 200
    assert "transactions" in res.json()


def test_balances_mock() -> None:
    res = client.get(f"/wallets/{ADDRESS}/balances")
    assert res.status_code == 200
    assert any(b["symbol"] == "SOL" for b in res.json()["balances"])
