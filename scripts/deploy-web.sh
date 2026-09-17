#!/usr/bin/env bash
# Build static Next export and deploy to Cloudflare Pages (project: chainlens).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_URL="${NEXT_PUBLIC_API_URL:?Set NEXT_PUBLIC_API_URL to your Render HTTPS URL}"

cd "${ROOT}/frontend"
NEXT_PUBLIC_API_URL="${API_URL}" npm run build
./node_modules/.bin/wrangler pages deploy out --project-name=chainlens --commit-dirty=true

echo "Pages: https://chainlens.ahmadmaulana.net (also https://chainlens-8or.pages.dev)"
echo "Set NEXT_PUBLIC_API_URL to your Render URL (https://….onrender.com)."
echo "Remember CORS_ORIGINS on Render includes https://chainlens.ahmadmaulana.net"
