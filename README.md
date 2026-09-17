# ChainLens — AI-powered Solana wallet intelligence

Portfolio MVP: Solana RPC → instruction parsing → LLM explanations → TiDB Cloud vectors.

## Live URLs

| Surface | URL |
|---------|-----|
| Frontend (custom domain) | https://chainlens.ahmadmaulana.net |
| Frontend (Cloudflare Pages) | https://chainlens-8or.pages.dev |
| API (Cloudflare Worker mock, interim) | https://chainlens-api.ahmadrizkimaulana666.workers.dev |
| Python API (AWS App Runner) | Via GitHub Actions Deploy workflow (see below) |

## Recruiter takeaway

> Understands Solana data, builds LLM product features, ships a full-stack MVP.

## What it does

- Connect a Solana wallet (Phantom / Solflare) or paste an address
- Fetch recent transactions via Solana JSON-RPC (`jsonParsed`)
- Decode SPL transfers and common program interactions
- Generate natural-language wallet summaries
- Store analyses with vector embeddings for similarity search (TiDB Cloud)

## Architecture

See [docs/architecture.md](docs/architecture.md) and [docs/requirements.md](docs/requirements.md).

```
Wallet address
  → Solana RPC (signatures + txs + balances)
  → instruction decoder
  → TiDB Cloud (JSON + VECTOR)
  → OpenAI structured summary
  → FastAPI (App Runner) → Next.js (Cloudflare Pages)
```

## Stack

| Layer | Choice |
|-------|--------|
| Frontend | Next.js (static export), TypeScript, Tailwind, Wallet Adapter → Cloudflare Pages |
| Backend | Python, FastAPI → AWS App Runner |
| Chain | Solana JSON-RPC |
| AI | OpenAI chat + embeddings |
| DB | TiDB Cloud (MySQL protocol + vector search) |
| Ops | GitHub Actions, Docker, pytest, Wrangler |

## Quick start (local)

```bash
cp .env.example .env
# Set DATABASE_URL to TiDB Cloud SQLAlchemy string (mysql+asyncmy://...?ssl=true)
# optional: OPENAI_API_KEY, SOLANA_RPC_URL; keep MOCK_ANALYZE=true for offline demo

cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

cd ../frontend
npm install
npm run dev
```

Open http://localhost:3000 — API docs at http://localhost:8000/docs

## Deploy (GitHub Actions)

Push to `main` runs [`.github/workflows/ci.yml`](.github/workflows/ci.yml) (pytest + frontend build) and [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) (ECR → App Runner + Cloudflare Pages).

Manual fallbacks remain in [`scripts/deploy-api.sh`](scripts/deploy-api.sh) and [`scripts/deploy-web.sh`](scripts/deploy-web.sh).

### One-time AWS: App Runner ECR access role

1. In IAM, create role **`AppRunnerECRAccessRole`**.
2. Trust principle: `build.apprunner.amazonaws.com`.
3. Attach policy allowing ECR pull (AWS managed **`AWSAppRunnerServicePolicyForECRAccess`** or equivalent).
4. Copy the role ARN into GitHub variable `APP_RUNNER_ECR_ACCESS_ROLE_ARN`.

### GitHub Secrets

| Name | Purpose |
|------|---------|
| `AWS_ACCESS_KEY_ID` | IAM user with ECR + App Runner permissions |
| `AWS_SECRET_ACCESS_KEY` | Pair for the access key |
| `CLOUDFLARE_API_TOKEN` | Token with **Account → Cloudflare Pages → Edit** |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account id (e.g. `9566706794f5e710b31e54379c39f104`) |
| `DATABASE_URL` | TiDB Cloud URL: `mysql+asyncmy://user:pass@host:4000/db?ssl=true` |
| `OPENAI_API_KEY` | Optional; leave empty while `MOCK_ANALYZE=true` |

### GitHub Variables

| Name | Example |
|------|---------|
| `AWS_REGION` | `ap-southeast-3` |
| `CORS_ORIGINS` | `https://chainlens.ahmadmaulana.net,https://chainlens-8or.pages.dev` |
| `MOCK_ANALYZE` | `true` |
| `SOLANA_RPC_URL` | `https://api.mainnet-beta.solana.com` |
| `NEXT_PUBLIC_API_URL` | Start with `https://chainlens-api.ahmadrizkimaulana666.workers.dev`, then switch to `https://….awsapprunner.com` (or later `https://api.chainlens.ahmadmaulana.net` if you CNAME the API) |
| `APP_RUNNER_ECR_ACCESS_ROLE_ARN` | `arn:aws:iam::ACCOUNT:role/AppRunnerECRAccessRole` |

### Custom domain DNS (`chainlens.ahmadmaulana.net`)

In Cloudflare Pages → project **chainlens** → **Custom domains** → add `chainlens.ahmadmaulana.net`.

If DNS for `ahmadmaulana.net` is on Cloudflare (recommended), Pages can auto-create the record. Otherwise at your DNS host:

| Type | Name | Target |
|------|------|--------|
| CNAME | `chainlens` | `chainlens-8or.pages.dev` |

Keep HTTPS on; wait for the certificate to become **Active**. Set GitHub variable `CORS_ORIGINS` to include `https://chainlens.ahmadmaulana.net`.

### First-time order

1. Add secrets/variables above (use Worker URL for `NEXT_PUBLIC_API_URL`).
2. Push `main` → Deploy workflow creates ECR image + App Runner + Pages.
3. Copy App Runner service URL from the workflow log.
4. Set `NEXT_PUBLIC_API_URL` to that HTTPS URL and re-run **Deploy** (or push an empty commit).

### Interim edge mock API

[`workers/mock-api`](workers/mock-api) keeps Pages usable before App Runner exists:

```bash
cd workers/mock-api && ../../frontend/node_modules/.bin/wrangler deploy
```

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness |
| GET | `/wallets/{address}/transactions` | Parsed timeline |
| GET | `/wallets/{address}/balances` | SOL + SPL balances |
| POST | `/wallets/{address}/summary` | AI summary |
| POST | `/analyze` | Full dashboard payload |
| GET | `/analyses/similar?q=` | Similar past analyses (TiDB vectors) |

```bash
curl -s -X POST http://localhost:8000/analyze \
  -H 'Content-Type: application/json' \
  -d '{"address":"11111111111111111111111111111111"}'
```

## Tests

```bash
cd backend && pytest
```

## Out of scope

- Multi-chain
- Full DEX IDL decoding
- Auth / rate limits / Redis
- Autonomous agents

## License

MIT — see [LICENSE](LICENSE)
