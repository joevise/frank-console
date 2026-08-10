#!/bin/bash
set -e
TOKEN=$(curl -s -X POST http://localhost:8100/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"joe","password":"frank2024"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -s -X POST http://localhost:8100/api/brief/generate \
  -H "Authorization: Bearer $TOKEN" \
  --max-time 180 \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"brief {d.get('date','')} rating={d.get('rating','')} OK\")"
