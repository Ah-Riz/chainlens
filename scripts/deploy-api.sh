#!/usr/bin/env bash
# API hosts on Render (free Web Service). Prefer dashboard auto-deploy from GitHub.
# Optional: export RENDER_DEPLOY_HOOK=... and run this script to force a deploy.
set -euo pipefail

: "${RENDER_DEPLOY_HOOK:?Set RENDER_DEPLOY_HOOK from Render → Service → Settings → Deploy Hook}"

curl -fsS -X POST "$RENDER_DEPLOY_HOOK"
echo
echo "Render deploy triggered."
