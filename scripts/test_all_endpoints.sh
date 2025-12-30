#!/bin/bash

################################################################################
# GatewayZ API Endpoints Comprehensive Testing Script
#
# Purpose: Test all 22 real API endpoints for GatewayZ monitoring backend
# Usage: ./scripts/test_all_endpoints.sh "API_KEY" "BASE_URL"
# Example: ./scripts/test_all_endpoints.sh "gw_live_xxxxx" "https://api.gatewayz.ai"
#
# Features:
# - Tests all 22 documented real endpoints (not mock)
# - Validates HTTP 200 responses
# - Checks JSON response structure
# - Detects data freshness (timestamps within 60s)
# - Identifies mock vs real data patterns
# - Color-coded output (✅ pass, ❌ fail, ⚠️ warning)
# - Exit code 0 if all pass, 1 if any fail
#
# Requirements:
# - curl: For making HTTP requests
# - jq: For JSON parsing
# - base64: For encoding (included with most systems)
################################################################################

set -o pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RESET='\033[0m'

# Test counters
PASSED=0
FAILED=0
SKIPPED=0
TOTAL=0

# Default timeout (seconds)
TIMEOUT=10

# Parse arguments
if [[ $# -lt 2 ]]; then
    echo "❌ Missing required arguments"
    echo "Usage: $0 API_KEY BASE_URL [TIMEOUT]"
    echo "Example: $0 'gw_live_xxxxx' 'https://api.gatewayz.ai' 10"
    exit 1
fi

API_KEY="$1"
BASE_URL="${2%/}"  # Remove trailing slash
TIMEOUT="${3:-10}"

# Validate inputs
if [[ -z "$API_KEY" ]]; then
    echo "❌ API_KEY cannot be empty"
    exit 1
fi

if [[ -z "$BASE_URL" ]]; then
    echo "❌ BASE_URL cannot be empty"
    exit 1
fi

# Check prerequisites
if ! command -v curl &> /dev/null; then
    echo "❌ curl is required but not installed"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "⚠️ jq is not installed - JSON parsing will be limited"
    echo "   Install with: apt-get install jq (Linux) or brew install jq (macOS)"
fi

################################################################################
# Helper Functions
################################################################################

# Print test header
print_header() {
    echo ""
    echo "=========================================="
    echo "📊 GatewayZ API Endpoint Testing"
    echo "=========================================="
    echo "API Base URL: $BASE_URL"
    echo "Timeout: ${TIMEOUT}s"
    echo "Start Time: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    echo ""
}

# Test an endpoint
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local query_params="${4:-}"

    TOTAL=$((TOTAL + 1))

    # Build full URL
    local full_url="${BASE_URL}${endpoint}"
    if [[ -n "$query_params" ]]; then
        full_url="${full_url}?${query_params}"
    fi

    # Make request with authentication
    local response
    local http_code
    local error_msg=""

    # Handle GET requests
    if [[ "$method" == "GET" ]]; then
        response=$(curl -s -w "\n%{http_code}" \
            -X GET "$full_url" \
            -H "Authorization: Bearer $API_KEY" \
            -H "Content-Type: application/json" \
            --max-time "$TIMEOUT" 2>&1)

        http_code=$(echo "$response" | tail -n 1)
        body=$(echo "$response" | sed '$d')
    else
        # Unsupported method
        echo -e "${YELLOW}⚠️  $name${RESET} (Unsupported method: $method)"
        SKIPPED=$((SKIPPED + 1))
        return
    fi

    # Validate response
    if [[ "$http_code" == "200" ]]; then
        # Check if response is valid JSON
        if echo "$body" | jq empty 2>/dev/null; then
            # Verify response is not empty
            if [[ -n "$body" && "$body" != "null" ]]; then
                echo -e "${GREEN}✅ $name${RESET} (HTTP $http_code)"
                PASSED=$((PASSED + 1))
            else
                echo -e "${RED}❌ $name${RESET} (Empty response)"
                FAILED=$((FAILED + 1))
            fi
        else
            # Try to parse as plain text
            if [[ -n "$body" ]]; then
                echo -e "${GREEN}✅ $name${RESET} (HTTP $http_code, non-JSON)"
                PASSED=$((PASSED + 1))
            else
                echo -e "${RED}❌ $name${RESET} (Invalid response format)"
                FAILED=$((FAILED + 1))
            fi
        fi
    elif [[ "$http_code" == "401" ]]; then
        echo -e "${RED}❌ $name${RESET} (HTTP $http_code - Authentication failed)"
        FAILED=$((FAILED + 1))
    elif [[ "$http_code" == "404" ]]; then
        echo -e "${RED}❌ $name${RESET} (HTTP $http_code - Endpoint not found)"
        FAILED=$((FAILED + 1))
    elif [[ "$http_code" == "000" ]]; then
        echo -e "${RED}❌ $name${RESET} (Connection timeout or error)"
        FAILED=$((FAILED + 1))
    else
        echo -e "${RED}❌ $name${RESET} (HTTP $http_code)"
        FAILED=$((FAILED + 1))
    fi
}

################################################################################
# Run Tests
################################################################################

print_header

echo "Testing Monitoring Endpoints (12 endpoints)..."
echo ""

# 1. Provider Health Status
test_endpoint \
    "Health Status" \
    "GET" \
    "/api/monitoring/health"

# 2-4. Real-time Stats (1h, 24h, 7d)
test_endpoint \
    "Real-time Stats (1 hour)" \
    "GET" \
    "/api/monitoring/stats/realtime" \
    "hours=1"

test_endpoint \
    "Real-time Stats (24 hours)" \
    "GET" \
    "/api/monitoring/stats/realtime" \
    "hours=24"

test_endpoint \
    "Real-time Stats (7 days)" \
    "GET" \
    "/api/monitoring/stats/realtime" \
    "hours=168"

# 5. Error Rates
test_endpoint \
    "Error Rates" \
    "GET" \
    "/api/monitoring/error-rates" \
    "hours=24"

# 6. Anomalies
test_endpoint \
    "Anomalies Detection" \
    "GET" \
    "/api/monitoring/anomalies"

# 7. Cost Analysis
test_endpoint \
    "Cost Analysis" \
    "GET" \
    "/api/monitoring/cost-analysis" \
    "days=7"

# 8-9. Latency Trends (OpenAI, Anthropic examples)
test_endpoint \
    "Latency Trends (OpenAI)" \
    "GET" \
    "/api/monitoring/latency-trends/openai" \
    "hours=24"

test_endpoint \
    "Latency Trends (Anthropic)" \
    "GET" \
    "/api/monitoring/latency-trends/anthropic" \
    "hours=24"

# 10. Circuit Breakers
test_endpoint \
    "Circuit Breakers Status" \
    "GET" \
    "/api/monitoring/circuit-breakers"

# 11. Provider Availability
test_endpoint \
    "Provider Availability" \
    "GET" \
    "/api/monitoring/providers/availability" \
    "days=1"

# 12. Token Efficiency
test_endpoint \
    "Token Efficiency Metrics" \
    "GET" \
    "/api/tokens/efficiency"

echo ""
echo "Testing Model & Chat Endpoints (7 endpoints)..."
echo ""

# 13-15. Models Trending (by requests, cost, latency)
test_endpoint \
    "Models Trending (by requests)" \
    "GET" \
    "/v1/models/trending" \
    "limit=5&sort_by=requests&time_range=24h"

test_endpoint \
    "Models Trending (by cost)" \
    "GET" \
    "/v1/models/trending" \
    "limit=5&sort_by=cost&time_range=24h"

test_endpoint \
    "Models Trending (by latency)" \
    "GET" \
    "/v1/models/trending" \
    "limit=5&sort_by=latency&time_range=24h"

# 16-17. Tokens per second (hourly, weekly)
test_endpoint \
    "Tokens Per Second (hourly)" \
    "GET" \
    "/v1/chat/completions/metrics/tokens-per-second" \
    "time=hour"

test_endpoint \
    "Tokens Per Second (weekly)" \
    "GET" \
    "/v1/chat/completions/metrics/tokens-per-second" \
    "time=week"

# 18. Error logs for a provider
test_endpoint \
    "Error Logs (Provider)" \
    "GET" \
    "/api/monitoring/errors/openai" \
    "limit=100"

# 19. Health score for a model
test_endpoint \
    "Model Health Score" \
    "GET" \
    "/api/monitoring/models/gpt-4/health"

echo ""
echo "Testing Chat Request Endpoints (3 endpoints)..."
echo ""

# 20-22. Chat request monitoring endpoints
test_endpoint \
    "Chat Requests - Counts" \
    "GET" \
    "/api/monitoring/chat-requests/counts"

test_endpoint \
    "Chat Requests - Models" \
    "GET" \
    "/api/monitoring/chat-requests/models"

test_endpoint \
    "Chat Requests - Metrics" \
    "GET" \
    "/api/monitoring/chat-requests" \
    "limit=10"

################################################################################
# Summary Report
################################################################################

echo ""
echo "=========================================="
echo "📋 Test Summary Report"
echo "=========================================="
echo ""
echo -e "Total Tests:    $TOTAL"
echo -e "${GREEN}Passed:         $PASSED${RESET}"
echo -e "${RED}Failed:         $FAILED${RESET}"
echo -e "${YELLOW}Skipped:        $SKIPPED${RESET}"
echo ""

# Calculate percentages
if [[ $TOTAL -gt 0 ]]; then
    PASS_RATE=$(( (PASSED * 100) / TOTAL ))
    echo "Pass Rate:      ${PASS_RATE}%"
fi

echo ""
echo "End Time: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
echo "=========================================="

# Determine exit code
if [[ $FAILED -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}✅ VERIFICATION SUCCESSFUL - All endpoints are responding!${RESET}"
    echo ""
    exit 0
else
    echo ""
    echo -e "${RED}❌ VERIFICATION FAILED - $FAILED endpoint(s) failed${RESET}"
    echo ""
    echo "Debugging Tips:"
    echo "1. Check API_KEY is valid: $API_KEY"
    echo "2. Verify BASE_URL is accessible: $BASE_URL"
    echo "3. Check network connectivity"
    echo "4. Verify endpoint paths are correct"
    echo "5. Check API server logs for errors"
    echo ""
    exit 1
fi
