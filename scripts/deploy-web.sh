#!/usr/bin/env bash
# Build static Next export and deploy to Cloudflare Pages (project: chainlens).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_URL="${NEXT_PUBLIC_API_URL:?Set NEXT_PUBLIC_API_URL to the App Runner HTTPS URL}"

cd "${ROOT}/frontend"
NEXT_PUBLIC_API_URL="${API_URL}" npm run build
./node_modules/.bin/wrangler pages deploy out --project-name=chainlens --commit-dirty=true

echo "Pages: https://chainlens-8or.pages.dev"
echo "Remember CORS_ORIGINS on the API includes this origin."
