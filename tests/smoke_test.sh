#!/usr/bin/env bash
# End-to-end smoke test: hit each endpoint and show the response.
# Run AFTER `docker compose up --build`.
set -euo pipefail

BASE="${1:-http://localhost:8000}"

echo "=== /api/health ==="
curl -sS "$BASE/api/health" | jq . 2>/dev/null || cat

echo -e "\n=== /api/branches ==="
curl -sS "$BASE/api/branches" | jq . 2>/dev/null || cat

echo -e "\n=== /api/products ==="
curl -sS "$BASE/api/products" | jq . 2>/dev/null || cat

echo -e "\n=== /api/stock ==="
curl -sS "$BASE/api/stock" | jq '.[0:3]' 2>/dev/null || cat

echo -e "\n=== POST /api/movements (restock Scranton copy paper) ==="
curl -sS -X POST "$BASE/api/movements" \
  -H "Content-Type: application/json" \
  -d '{"product_id":1,"branch_id":1,"change_qty":50,"reason":"restock"}' 2>/dev/null || true

echo -e "\n=== /api/alerts ==="
curl -sS "$BASE/api/alerts" | jq . 2>/dev/null || cat

echo -e "\n=== /api/stats/depletion-rate ==="
curl -sS "$BASE/api/stats/depletion-rate?days=7" | jq . 2>/dev/null || cat

echo -e "\nDone."