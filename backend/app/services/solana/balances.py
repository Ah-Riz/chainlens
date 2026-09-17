from __future__ import annotations

from app.schemas import TokenBalance
from app.services.solana.programs import mint_symbol
from app.services.solana.rpc import SolanaRpc


async def fetch_balances(address: str, rpc: SolanaRpc | None = None) -> list[TokenBalance]:
    client = rpc or SolanaRpc()
    balances: list[TokenBalance] = []

    lamports = await client.get_balance(address)
    balances.append(
        TokenBalance(
            mint="So11111111111111111111111111111111111111112",
            symbol="SOL",
            amount=f"{lamports / 1e9:.6f}".rstrip("0").rstrip("."),
            decimals=9,
        )
    )

    accounts = await client.get_token_accounts_by_owner(address)
    for acct in accounts:
        info = (
            ((acct.get("account") or {}).get("data") or {}).get("parsed") or {}
        ).get("info") or {}
        token_amount = info.get("tokenAmount") or {}
        amount_str = token_amount.get("uiAmountString") or "0"
        if amount_str in {"0", "0.0", "0.00"}:
            continue
        mint = info.get("mint") or ""
        symbol, decimals = mint_symbol(mint)
        if decimals == 0:
            decimals = int(token_amount.get("decimals") or 0)
        balances.append(
            TokenBalance(mint=mint, symbol=symbol, amount=amount_str, decimals=decimals)
        )

    return balances
