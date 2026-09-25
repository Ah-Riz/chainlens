from app.services.address import is_valid_solana_address

# Well-known Solana system program — valid 32-byte pubkey
SYSTEM_PROGRAM = "11111111111111111111111111111111"


def test_accepts_system_program() -> None:
    assert is_valid_solana_address(SYSTEM_PROGRAM)


def test_rejects_eth_address() -> None:
    assert not is_valid_solana_address("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")


def test_rejects_short() -> None:
    assert not is_valid_solana_address("abc")


def test_strips_whitespace_for_validation() -> None:
    assert is_valid_solana_address(f"  {SYSTEM_PROGRAM}  ")
