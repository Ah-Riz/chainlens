# ChainLens — AI-powered Solana wallet intelligence

Portfolio MVP: Solana RPC → instruction parsing → LLM explanations → TiDB Cloud vectors.

## Live URLs

| Surface | URL |
|---------|-----|
| Frontend (custom domain) | https://chainlens.ahmadmaulana.net |
| Frontend (Cloudflare Pages) | https://chainlens-8or.pages.dev |
| API (Render free Web Service) | `https://chainlens-api-….onrender.com` (set after first Render deploy) |
| API (Cloudflare Worker mock, optional) | https://chainlens-api.ahmadrizkimaulana666.workers.dev |

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
  → FastAPI (Render) → Next.js (Cloudflare Pages)
```

## Stack

| Layer | Choice |
|-------|--------|
| Frontend | Next.js (static export), TypeScript, Tailwind, Wallet Adapter → Cloudflare Pages |
| Backend | Python, FastAPI → Render (free Web Service) |
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

## Deploy

### Backend → Render (free)

1. Open [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint** → connect `Ah-Riz/chainlens`.
2. Apply [`render.yaml`](render.yaml) (service `chainlens-api`, Python, `rootDir: backend`, free plan).
   - If you already created a Web Service manually: set **Root Directory** to `backend`, build `pip install -r requirements.txt`, and **Start Command** to `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (not the default `gunicorn your_application.wsgi`).
3. In the service **Environment**, set:
   - `DATABASE_URL` — TiDB `mysql+asyncmy://...?ssl=true`
   - `OPENAI_API_KEY` — optional if `MOCK_ANALYZE=true`
   - Confirm `CORS_ORIGINS` includes `https://chainlens.ahmadmaulana.net`
4. Copy the service URL (`https://….onrender.com`).
5. Free tier **spins down when idle** — first request after idle can take ~30–60s.

Auto-deploy on push to `main` is enabled in the Blueprint. Optional GitHub secret `RENDER_DEPLOY_HOOK` triggers an extra deploy from Actions.

### Frontend → Cloudflare Pages (GitHub Actions)

Push to `main` runs [`.github/workflows/ci.yml`](.github/workflows/ci.yml) and [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) (Pages + optional Render hook).

### GitHub Secrets

| Name | Purpose |
|------|---------|
| `CLOUDFLARE_API_TOKEN` | Pages deploy (Account → Cloudflare Pages → Edit) |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account id |
| `RENDER_DEPLOY_HOOK` | Optional; Render → Service → Settings → Deploy Hook |

### GitHub Variables

| Name | Example |
|------|---------|
| `NEXT_PUBLIC_API_URL` | `https://chainlens-api-xxxx.onrender.com` (your Render URL) |

### Render environment (dashboard)

| Name | Example |
|------|---------|
| `DATABASE_URL` | TiDB Cloud SQLAlchemy URL |
| `CORS_ORIGINS` | `https://chainlens.ahmadmaulana.net,https://chainlens-8or.pages.dev,http://localhost:3000` |
| `MOCK_ANALYZE` | `true` |
| `SOLANA_RPC_URL` | `https://api.mainnet-beta.solana.com` |
| `OPENAI_API_KEY` | optional |

### Custom domain DNS (`chainlens.ahmadmaulana.net`)

Cloudflare Pages → project **chainlens** → **Custom domains**. CNAME `chainlens` → `chainlens-8or.pages.dev` if DNS is external.

### First-time order

1. Create Render service from Blueprint; set env; wait until live.
2. Set GitHub `NEXT_PUBLIC_API_URL` to the Render HTTPS URL.
3. Ensure Cloudflare secrets exist; push `main` (or re-run **Deploy**) so Pages rebuilds against Render.

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
- Paid AWS App Runner hosting

## License

MIT — see [LICENSE](LICENSE)
