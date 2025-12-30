#!/bin/bash

# Real Instrumentation Endpoints for Loki Testing
# These are NOT mock data - they're your actual API endpoints

BASE_URL="${1:-https://api.gatewayz.ai}"
API_KEY="${2:-your-api-key}"

echo "🚀 Testing Loki with REAL Instrumentation Endpoints"
echo "=========================================================="
echo "Base URL: $BASE_URL"
echo ""

# Step 1: Check Instrumentation Health
echo "1️⃣  Checking Instrumentation Health..."
curl -s -X GET "$BASE_URL/api/instrumentation/health" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" | jq '.' || echo "Health check failed"
echo ""

# Step 2: Check Loki Status
echo "2️⃣  Checking Loki Status..."
curl -s -X GET "$BASE_URL/api/instrumentation/loki/status" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" | jq '.' || echo "Loki status check failed"
echo ""

# Step 3: Send Real Test Logs to Loki (using actual endpoint)
echo "3️⃣  Sending REAL test logs to Loki..."
for i in {1..5}; do
  echo "  Sending test log #$i..."
  curl -s -X POST "$BASE_URL/api/instrumentation/test-log" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{
      \"message\": \"GatewayZ Real Instrumentation Log #$i\",
      \"level\": \"info\",
      \"service\": \"gatewayz-api\",
      \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
    }" | jq '.' || echo "Failed to send log #$i"
  
  sleep 1
done

echo ""
echo "4️⃣  Sending Real Test Traces to Tempo..."
for i in {1..3}; do
  echo "  Sending test trace #$i..."
  curl -s -X POST "$BASE_URL/api/instrumentation/test-trace" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{
      \"operation\": \"test_operation_$i\",
      \"service\": \"gatewayz-api\",
      \"duration_ms\": $((RANDOM % 500 + 50))
    }" | jq '.' || echo "Failed to send trace #$i"
  
  sleep 1
done

echo ""
echo "✅ Real instrumentation test complete"
echo ""
echo "Next Steps:"
echo "1. Wait 10 seconds for logs to propagate to Loki"
echo "2. Go to Grafana Loki Logs dashboard"
echo "3. Refresh the dashboard to see the real logs"
echo "4. Should see entries from service=gatewayz-api"

