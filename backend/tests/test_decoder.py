from app.services.solana.decoder import decode_transaction

WALLET = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"


def test_decode_system_transfer_in() -> None:
    tx = {
        "blockTime": 1700000000,
        "slot": 1,
        "transaction": {
            "message": {
                "instructions": [
                    {
                        "program": "system",
                        "programId": "11111111111111111111111111111111",
                        "parsed": {
                            "type": "transfer",
                            "info": {
                                "source": "Sender1111111111111111111111111111111111111",
                                "destination": WALLET,
                                "lamports": 1_000_000_000,
                            },
                        },
                    }
                ]
            }
        },
        "meta": {},
    }
    event = decode_transaction("SigA", tx, WALLET)
    assert event.tx_type == "SOL_TRANSFER"
    assert "received" in event.description
    assert "1.0000 SOL" in event.description


def test_decode_spl_transfer() -> None:
    tx = {
        "blockTime": 1700000001,
        "slot": 2,
        "transaction": {
            "message": {
                "instructions": [
                    {
                        "program": "spl-token",
                        "programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
                        "parsed": {
                            "type": "transferChecked",
                            "info": {
                                "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                                "authority": WALLET,
                                "source": "TokenAcct111111111111111111111111111111111",
                                "destination": "TokenAcct222222222222222222222222222222222",
                                "tokenAmount": {"uiAmountString": "10.5", "decimals": 6},
                            },
                        },
                    }
                ]
            }
        },
        "meta": {},
    }
    event = decode_transaction("SigB", tx, WALLET)
    assert event.tx_type == "SPL_TRANSFER"
    assert "USDC" in event.description


def test_decode_jupiter_swap_hint() -> None:
    tx = {
        "blockTime": 1700000002,
        "slot": 3,
        "transaction": {
            "message": {
                "instructions": [
                    {
                        "programId": "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",
                        "data": "xx",
                    },
                    {
                        "program": "spl-token",
                        "programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
                        "parsed": {
                            "type": "transfer",
                            "info": {
                                "mint": "So11111111111111111111111111111111111111112",
                                "authority": WALLET,
                                "amount": "100",
                            },
                        },
                    },
                ]
            }
        },
        "meta": {},
    }
    event = decode_transaction("SigC", tx, WALLET)
    assert event.tx_type == "SWAP_HINT"
    assert "Jupiter" in event.description


def test_decode_missing_tx() -> None:
    event = decode_transaction("SigD", None, WALLET)
    assert event.tx_type == "UNKNOWN"
