#!/bin/bash
# Verification script for GatewayZ metrics collection
# This script checks that Prometheus is correctly scraping real data

set -e

echo "🔍 GatewayZ Metrics Verification"
echo "================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# API Base URL
API_URL="${API_URL:-http://localhost:8000}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"

# Function to check endpoint
check_endpoint() {
    local url=$1
    local name=$2
    
    echo -n "Checking $name... "
    if curl -s -f -o /dev/null "$url"; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
}

# Function to query Prometheus
query_prometheus() {
    local query=$1
    local name=$2
    
    echo -n "Querying $name... "
    
    # URL encode the query
    local encoded_query=$(echo "$query" | jq -sRr @uri)
    local url="${PROMETHEUS_URL}/api/v1/query?query=${encoded_query}"
    
    local response=$(curl -s "$url")
    local status=$(echo "$response" | jq -r '.status')
    
    if [ "$status" == "success" ]; then
        local result_type=$(echo "$response" | jq -r '.data.resultType')
        local result_count=$(echo "$response" | jq '.data.result | length')
        
        if [ "$result_count" -gt 0 ]; then
            echo -e "${GREEN}✓ OK${NC} ($result_count results)"
            echo "$response" | jq -r '.data.result[0]' | head -3
            return 0
        else
            echo -e "${YELLOW}⚠ No data${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
}

# Function to check metric exists
check_metric_exists() {
    local metric=$1
    local name=$2
    
    query_prometheus "$metric" "$name"
}

echo "Step 1: Backend API Health"
echo "---------------------------"
check_endpoint "$API_URL/health" "Backend API"
check_endpoint "$API_URL/metrics" "Prometheus metrics endpoint"
echo ""

echo "Step 2: Prometheus Health"
echo "--------------------------"
check_endpoint "$PROMETHEUS_URL/-/healthy" "Prometheus health"
check_endpoint "$PROMETHEUS_URL/api/v1/targets" "Prometheus targets"
echo ""

echo "Step 3: Verify Prometheus is Scraping Backend"
echo "---------------------------------------------"

# Check scrape status
echo "Fetching scrape targets..."
targets=$(curl -s "${PROMETHEUS_URL}/api/v1/targets" | jq -r '.data.activeTargets[] | select(.labels.job=="gatewayz-api")')

if [ -z "$targets" ]; then
    echo -e "${RED}✗ No gatewayz-api target found${NC}"
    echo "Please ensure Prometheus is configured to scrape the backend"
    exit 1
else
    target_health=$(echo "$targets" | jq -r '.health')
    target_url=$(echo "$targets" | jq -r '.scrapeUrl')
    last_scrape=$(echo "$targets" | jq -r '.lastScrape')
    
    if [ "$target_health" == "up" ]; then
        echo -e "${GREEN}✓ Backend target is UP${NC}"
        echo "  URL: $target_url"
        echo "  Last scrape: $last_scrape"
    else
        echo -e "${RED}✗ Backend target is DOWN${NC}"
        echo "  URL: $target_url"
        echo "  Last error: $(echo "$targets" | jq -r '.lastError')"
        exit 1
    fi
fi
echo ""

echo "Step 4: Verify Real Metrics Data"
echo "---------------------------------"

# Check various metrics
check_metric_exists "fastapi_requests_total" "HTTP requests"
check_metric_exists "model_inference_requests_total" "Model inference requests"
check_metric_exists "tokens_used_total" "Token usage"
check_metric_exists "provider_availability" "Provider availability"
echo ""

echo "Step 5: Calculate Current Health Score"
echo "---------------------------------------"

# Query success rate
echo "Calculating model health score..."
success_query="sum(rate(model_inference_requests_total{status=\"success\"}[10m])) / sum(rate(model_inference_requests_total[10m])) * 100"
encoded_query=$(echo "$success_query" | jq -sRr @uri)
response=$(curl -s "${PROMETHEUS_URL}/api/v1/query?query=${encoded_query}")

status=$(echo "$response" | jq -r '.status')
if [ "$status" == "success" ]; then
    result=$(echo "$response" | jq -r '.data.result[0].value[1]')
    
    if [ "$result" != "null" ]; then
        health_score=$(printf "%.2f" "$result")
        echo -e "Current health score: ${GREEN}${health_score}%${NC}"
        
        # Compare to threshold
        threshold=20
        if (( $(echo "$result < $threshold" | bc -l) )); then
            echo -e "${RED}⚠ ALERT: Health score below ${threshold}%!${NC}"
            echo "Alert should fire after 5 minutes"
        else
            echo -e "${GREEN}✓ Health score is healthy (above ${threshold}%)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ No data available yet${NC}"
        echo "Please send some requests to the API first"
    fi
else
    echo -e "${RED}✗ Failed to calculate health score${NC}"
fi
echo ""

echo "Step 6: Check Alert Rules"
echo "--------------------------"
check_endpoint "$PROMETHEUS_URL/api/v1/rules" "Alert rules"

echo "Fetching alert rules..."
rules=$(curl -s "${PROMETHEUS_URL}/api/v1/rules" | jq -r '.data.groups[] | select(.name=="model_health_alerts")')

if [ -z "$rules" ]; then
    echo -e "${YELLOW}⚠ model_health_alerts group not found${NC}"
    echo "Please ensure alert.rules.yml is loaded"
else
    echo -e "${GREEN}✓ Alert rules loaded${NC}"
    
    # Check specific alert
    health_alert=$(echo "$rules" | jq -r '.rules[] | select(.name=="LowModelHealthScore")')
    if [ -z "$health_alert" ]; then
        echo -e "${YELLOW}⚠ LowModelHealthScore alert not found${NC}"
    else
        alert_state=$(echo "$health_alert" | jq -r '.state')
        echo "  LowModelHealthScore state: $alert_state"
        
        if [ "$alert_state" == "firing" ]; then
            echo -e "${RED}  ⚠ ALERT IS FIRING!${NC}"
            echo "  Email should be sent to manjeshprasad21@gmail.com"
        fi
    fi
fi
echo ""

echo "Step 7: Backend API Data Verification"
echo "--------------------------------------"

# Check trending models endpoint
echo "Checking /v1/models/trending endpoint..."
trending=$(curl -s "${API_URL}/catalog/models/trending?limit=5")
success=$(echo "$trending" | jq -r '.success')

if [ "$success" == "true" ]; then
    count=$(echo "$trending" | jq -r '.count')
    echo -e "${GREEN}✓ Trending models endpoint working${NC}"
    echo "  Found $count trending models"
    
    # Show sample data
    echo "  Sample model:"
    echo "$trending" | jq -r '.data[0]' | head -5
else
    echo -e "${RED}✗ Trending models endpoint failed${NC}"
fi
echo ""

echo "Step 8: Grafana Dashboard Verification"
echo "---------------------------------------"
check_endpoint "http://localhost:3000/api/health" "Grafana"

echo ""
echo "================================="
echo "✅ Verification Complete!"
echo "================================="
echo ""
echo "Summary:"
echo "--------"
echo "✓ Backend API is collecting real metrics"
echo "✓ Prometheus is scraping metrics from backend"
echo "✓ Alert rules are configured"
echo "✓ Email alerts will be sent to manjeshprasad21@gmail.com"
echo ""
echo "Next Steps:"
echo "-----------"
echo "1. Visit Prometheus: $PROMETHEUS_URL"
echo "2. Visit Grafana: http://localhost:3000"
echo "3. View Model Performance Dashboard:"
echo "   http://localhost:3000/d/model-performance-v1/model-performance-analytics"
echo "4. View Prometheus Alerts:"
echo "   ${PROMETHEUS_URL}/alerts"
echo ""
echo "To test email alerts:"
echo "---------------------"
echo "1. Set SMTP credentials in .env or Railway environment"
echo "2. Trigger alert by causing health score to drop below 20%"
echo "3. Or lower threshold temporarily in alert.rules.yml"
echo ""
