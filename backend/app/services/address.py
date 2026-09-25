from __future__ import annotations

import base58

# Solana ed25519 pubkeys are 32 bytes when decoded from base58.


def is_valid_solana_address(address: str) -> bool:
    if not address or not isinstance(address, str):
        return False
    try:
        raw = base58.b58decode(address.strip())
    except Exception:
        return False
    return len(raw) == 32
