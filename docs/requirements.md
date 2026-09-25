# ChainLens requirements

## Business objective

Help Solana users understand wallet behavior without reading raw blockchain data.

## User stories

1. As a user, I want to paste a Solana address so I can analyze any wallet.
2. As a user, I want an activity mix of recent on-chain behavior so I can see what the wallet does without reading raw txs.
3. As a user, I want token balances so I can see what the wallet holds.
4. As a user, I want an AI summary so I can understand patterns quickly.

## Acceptance criteria (EARS)

1. WHEN the user submits a valid Solana base58 pubkey THEN the system SHALL return analysis within the configured tx window.
2. WHEN the user submits an invalid address THEN the system SHALL respond with HTTP 400.
3. WHEN Solana RPC fails THEN the system SHALL respond with HTTP 502 and a clear error detail.
4. WHEN a wallet has no recent transactions THEN the system SHALL return HTTP 200 with empty transaction lists.
5. WHEN `MOCK_ANALYZE=true` OR the Gemini key is missing/implausible THEN the system SHALL return a rule-based summary with `mock: true`.
6. WHEN the primary Gemini model returns 503/429/UNAVAILABLE or a 404 “no longer available to new users” THEN the system SHALL try the configured fallback flash models and set `fallback_used` when a later model answers.

## Edge cases

- Empty wallet / new account
- RPC rate limits / timeouts
- Transactions with unknown programs (label as unknown, still include)
- LLM timeout → fall back to rule-based summary when possible

## Deferred (not MVP)

- Wallet Adapter connect flow
- Chronological per-transaction timeline UI
- Similarity search / embedding persist in the product UI

## Out of scope

Multi-chain, auth, Redis, full DEX IDL decode, agent loops, streaming indexer.
