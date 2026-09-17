# ChainLens requirements

## Business objective

Help Solana users understand wallet behavior without reading raw blockchain data.

## User stories

1. As a user, I want to paste a Solana address so I can analyze any wallet.
2. As a user, I want to connect my wallet so I can analyze my own activity without typing an address.
3. As a user, I want a transaction timeline so I can see recent activity in plain language.
4. As a user, I want token balances so I can see what the wallet holds.
5. As a user, I want an AI summary so I can understand patterns quickly.

## Acceptance criteria (EARS)

1. WHEN the user submits a valid Solana base58 pubkey THEN the system SHALL return analysis within the configured tx window.
2. WHEN the user submits an invalid address THEN the system SHALL respond with HTTP 400.
3. WHEN Solana RPC fails THEN the system SHALL respond with HTTP 502 and a clear error detail.
4. WHEN a wallet has no recent transactions THEN the system SHALL return HTTP 200 with empty transaction lists.
5. WHEN `MOCK_ANALYZE=true` OR the OpenAI key is missing THEN the system SHALL return a rule-based summary with `mock: true`.
6. WHEN analysis completes with a live LLM THEN the system SHALL persist the summary embedding in Postgres (pgvector).
7. WHEN the user requests similar analyses AND embeddings exist THEN the system SHALL return top-k cosine matches.
8. IF Wallet Adapter connects successfully THEN the UI SHALL populate the address field with the connected pubkey.

## Edge cases

- Empty wallet / new account
- RPC rate limits / timeouts
- Transactions with unknown programs (label as unknown, still include)
- LLM timeout → fall back to rule-based summary when possible

## Out of scope

Multi-chain, auth, Redis, full DEX IDL decode, agent loops, streaming indexer.
