#!/usr/bin/env bash
# Wake Render free-tier API before a demo (~30–60s cold start).
set -euo pipefail
API="${1:-https://chainlens-fok6.onrender.com}"
curl -fsS -m 90 "$API/health"
echo
