from __future__ import annotations

from typing import Any

import httpx
from fastapi import HTTPException

from app.config import settings


class SolanaRpc:
    def __init__(self, url: str | None = None, timeout: float = 30.0) -> None:
        self.url = url or settings.solana_rpc_url
        self.timeout = timeout

    async def _call(self, method: str, params: list[Any]) -> Any:
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(self.url, json=payload)
                res.raise_for_status()
                body = res.json()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Solana RPC error: {exc}") from exc
        if "error" in body:
            raise HTTPException(status_code=502, detail=f"Solana RPC error: {body['error']}")
        return body.get("result")

    async def get_signatures_for_address(self, address: str, limit: int) -> list[dict[str, Any]]:
        result = await self._call(
            "getSignaturesForAddress",
            [address, {"limit": limit}],
        )
        return result or []

    async def get_transaction(self, signature: str) -> dict[str, Any] | None:
        return await self._call(
            "getTransaction",
            [signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 1}],
        )

    async def get_balance(self, address: str) -> int:
        result = await self._call("getBalance", [address])
        return int((result or {}).get("value", 0))

    async def get_token_accounts_by_owner(self, address: str) -> list[dict[str, Any]]:
        result = await self._call(
            "getTokenAccountsByOwner",
            [
                address,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                {"encoding": "jsonParsed"},
            ],
        )
        return (result or {}).get("value") or []
