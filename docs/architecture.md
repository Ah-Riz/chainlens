# ChainLens architecture

## Goal

Solana wallet intelligence: RPC → parse instructions → structured activity → LLM explanation. Optional best-effort TiDB JSON cache when `DATABASE_URL` is set.

## Pipeline

```mermaid
flowchart LR
  UI[Next.js paste address] --> API[FastAPI]
  API --> RPC[Solana JSON-RPC]
  RPC --> Parser[Instruction decoder]
  Parser --> Pipeline[Structured activity]
  Pipeline --> LLM[Gemini summary]
  Pipeline --> Store[(TiDB Cloud optional)]
  LLM --> Store
  Store --> API
  API --> UI
```

## Components

| Component | Responsibility |
|-----------|----------------|
| Frontend | Paste address, dashboard (Cloudflare Pages) |
| `POST /analyze` | Orchestrate fetch → parse → LLM → optional persist |
| Solana RPC client | Signatures, txs (`jsonParsed`), balances |
| Decoder | SPL transfers, program labels, activity events |
| LLM | Narrative / structured summary (Gemini + rule-based fallback) |
| TiDB Cloud | Best-effort JSON cache of analyses (optional) |

## Deploy

| Layer | Host |
|-------|------|
| Frontend | Cloudflare Pages — https://chainlens.ahmadmaulana.net |
| API | Render free Web Service — https://chainlens-fok6.onrender.com (`render.yaml`) |
| DB | TiDB Cloud Starter (optional JSON cache) |


## Error handling

| Condition | Response |
|-----------|----------|
| Invalid address | 400 |
| RPC failure | 502 |
| Empty history | 200 + empty lists |
| Missing LLM key (live mode) | Rule-based summary + `mock: true` |

## Non-goals

Multi-chain, agents, Redis, Alembic, full DEX IDL decoding, Wallet Adapter, vector similarity search.
