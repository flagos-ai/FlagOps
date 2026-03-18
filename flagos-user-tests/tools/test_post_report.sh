#!/bin/bash
# Local test script for posting test cases report.
#
# Usage:
#   ./tools/test_post_report.sh <backend_url> [api_token]
#
# Example:
#   ./tools/test_post_report.sh http://10.0.0.1:8080
#   ./tools/test_post_report.sh http://10.0.0.1:8080 my-secret-token

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

BACKEND_URL="${1:?Usage: $0 <backend_url> [api_token]}"
BACKEND_URL="${BACKEND_URL%/}"
API_TOKEN="${2:-}"

LIST_CODE="flagops-user-test-cases"
LIST_NAME="FlagOps User Test Cases"
REPORT_PATH="$ROOT_DIR/test_cases_report.json"

HEADER_CONFIG='[
  {"field": "case_id",    "name": "用例ID",     "required": true,  "sortable": true,  "type": "string"},
  {"field": "case_name",  "name": "用例名称",   "required": true,  "sortable": false, "type": "string"},
  {"field": "repo",       "name": "所属子仓库", "required": true,  "sortable": true,  "type": "string"},
  {"field": "updated_at", "name": "更新时间",   "required": true,  "sortable": true,  "type": "string"}
]'

# --- Step 1: Collect test cases ---
echo "=== Step 1: Collect test cases ==="
cd "$ROOT_DIR"
python tools/collect_test_cases.py --root . --output "$REPORT_PATH"
echo "Report content:"
cat "$REPORT_PATH" | python -m json.tool
echo ""

# --- Step 2: Post header config ---
echo "=== Step 2: Post header config ==="
HEADER_PAYLOAD=$(jq -n \
  --arg list_code "$LIST_CODE" \
  --arg list_name "$LIST_NAME" \
  --argjson header_config "$HEADER_CONFIG" \
  '{list_code: $list_code, list_name: $list_name, header_config: $header_config}')

echo "URL: ${BACKEND_URL}/flagcicd-backend/list/header"
echo "Payload:"
echo "$HEADER_PAYLOAD" | jq .

CURL_ARGS=(-s -X POST -w '\n%{http_code}' -H "Content-Type: application/json" -d "$HEADER_PAYLOAD")
[ -n "$API_TOKEN" ] && CURL_ARGS+=(-H "Authorization: Bearer $API_TOKEN")

RESPONSE=$(curl "${CURL_ARGS[@]}" "${BACKEND_URL}/flagcicd-backend/list/header")
HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')

echo "HTTP status: $HTTP_STATUS"
echo "Response: $RESPONSE_BODY"
echo ""

# --- Step 3: Post list data ---
echo "=== Step 3: Post list data ==="
COMMIT_ID="$(git rev-parse HEAD 2>/dev/null || echo 'unknown')"
REPO_NAME="flagos-ai/FlagOps"
WORKFLOW_ID="local-test"
RUN_ID="local-$$"

DATA_PAYLOAD=$(jq -n \
  --arg repository_name "$REPO_NAME" \
  --slurpfile report "$REPORT_PATH" \
  '{
    items: [ $report[0][] | . + {
      repository_name: $repository_name
    } ]
  }')

echo "URL: ${BACKEND_URL}/flagcicd-backend/list/data/${LIST_CODE}"
echo "Items count: $(echo "$DATA_PAYLOAD" | jq '.items | length')"
echo "Payload (first item sample):"
echo "$DATA_PAYLOAD" | jq '{items_count: (.items | length), first_item: .items[0]}'

CURL_ARGS=(-s -X POST -w '\n%{http_code}' -H "Content-Type: application/json" -d "$DATA_PAYLOAD")
[ -n "$API_TOKEN" ] && CURL_ARGS+=(-H "Authorization: Bearer $API_TOKEN")

RESPONSE=$(curl "${CURL_ARGS[@]}" "${BACKEND_URL}/flagcicd-backend/list/data/${LIST_CODE}")
HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')

echo "HTTP status: $HTTP_STATUS"
echo "Response: $RESPONSE_BODY"
echo ""

# --- Step 4: Query to verify ---
echo "=== Step 4: Query list data ==="
QUERY_URL="${BACKEND_URL}/flagcicd-backend/list/data/${LIST_CODE}?page_size=10&page=1&sort=created_at&order=desc"
echo "URL: $QUERY_URL"

CURL_ARGS=(-s -X GET -w '\n%{http_code}' -H "Accept: application/json")
[ -n "$API_TOKEN" ] && CURL_ARGS+=(-H "Authorization: Bearer $API_TOKEN")

RESPONSE=$(curl "${CURL_ARGS[@]}" "$QUERY_URL")
HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')

echo "HTTP status: $HTTP_STATUS"
echo "Response:"
echo "$RESPONSE_BODY" | jq . 2>/dev/null || echo "$RESPONSE_BODY"

# Cleanup
rm -f "$REPORT_PATH"
echo ""
echo "=== Done ==="
