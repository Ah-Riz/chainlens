from app.services.solana.account_kind import (
    SYSTEM_PROGRAM,
    TOKEN_PROGRAM,
    classify_account,
    classify_with_address_label,
)

KLEND = "KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD"


def test_program_klend() -> None:
    info = {"executable": True, "owner": "BPFLoaderUpgradeab1e11111111111111111111111"}
    c = classify_with_address_label(info, KLEND)
    assert c.kind == "program"
    assert c.owner_label == "KLend"
    assert "program" in c.what_is_this.lower()
    assert "wallet" in c.what_is_this.lower()  # "not a personal wallet"


def test_protocol_vault_owned_by_klend() -> None:
    info = {"executable": False, "owner": KLEND, "data": {}}
    c = classify_account(info)
    assert c.kind == "protocol_account"
    assert c.owner_label == "KLend"
    assert "KLend" in c.what_is_this
    assert "not a personal wallet" in c.what_is_this.lower()


def test_token_mint() -> None:
    info = {
        "executable": False,
        "owner": TOKEN_PROGRAM,
        "data": {"program": "spl-token", "parsed": {"type": "mint", "info": {}}},
    }
    c = classify_account(info)
    assert c.kind == "token_mint"
    assert "mint" in c.what_is_this.lower()


def test_token_account() -> None:
    info = {
        "executable": False,
        "owner": TOKEN_PROGRAM,
        "data": {"program": "spl-token", "parsed": {"type": "account", "info": {}}},
    }
    c = classify_account(info)
    assert c.kind == "token_account"


def test_wallet_system() -> None:
    info = {"executable": False, "owner": SYSTEM_PROGRAM, "data": {}}
    c = classify_account(info)
    assert c.kind == "wallet"
    assert "wallet" in c.what_is_this.lower()


def test_unknown_missing() -> None:
    c = classify_account(None)
    assert c.kind == "unknown"
