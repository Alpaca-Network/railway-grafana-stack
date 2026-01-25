#!/bin/bash
# Test the full data flow: Prometheus → Mimir → Grafana
# Run this on Railway to verify everything is connected

set -e

echo "=================================================="
echo "Testing Prometheus → Mimir → Grafana Data Flow"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

# Function to check URL accessibility
check_url() {
    local url=$1
    local name=$2
    if curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" | grep -q "200\|302"; then
        print_status 0 "$name is accessible"
        return 0
    else
        print_status 1 "$name is NOT accessible"
        return 1
    fi
}

echo "Step 1: Check Service Accessibility"
echo "------------------------------------"

# Check Prometheus
PROM_URL="${PROMETHEUS_INTERNAL_URL:-http://prometheus.railway.internal:9090}"
check_url "$PROM_URL/-/healthy" "Prometheus ($PROM_URL)"
PROM_OK=$?

# Check Mimir
MIMIR_URL="${MIMIR_INTERNAL_URL:-http://mimir.railway.internal:9009}"
check_url "$MIMIR_URL/ready" "Mimir ($MIMIR_URL)"
MIMIR_OK=$?

# Check Grafana
GRAFANA_URL="${GRAFANA_INTERNAL_URL:-http://grafana.railway.internal:3000}"
check_url "$GRAFANA_URL/api/health" "Grafana ($GRAFANA_URL)"
GRAFANA_OK=$?

echo ""
echo "Step 2: Check Prometheus Configuration"
echo "---------------------------------------"

# Check if Prometheus has Mimir in remote_write config
PROM_CONFIG=$(curl -s "$PROM_URL/api/v1/status/config" 2>/dev/null || echo "{}")
if echo "$PROM_CONFIG" | grep -q "mimir.*api/v1/push"; then
    print_status 0 "Prometheus has Mimir remote_write configured"
    PROM_REMOTE_WRITE_OK=0
    
    # Extract the URL
    REMOTE_WRITE_URL=$(echo "$PROM_CONFIG" | grep -o 'http[s]*://[^"]*api/v1/push' | head -1)
    echo "  Remote write URL: $REMOTE_WRITE_URL"
    
    # Check if using internal link
    if echo "$REMOTE_WRITE_URL" | grep -q "railway.internal"; then
        print_status 0 "Using Railway internal network ✓"
    else
        print_status 1 "NOT using Railway internal network (using: $REMOTE_WRITE_URL)"
    fi
else
    print_status 1 "Prometheus does NOT have Mimir remote_write configured"
    PROM_REMOTE_WRITE_OK=1
fi

echo ""
echo "Step 3: Check Prometheus → Mimir Data Flow"
echo "-------------------------------------------"

# Check Prometheus remote write status
PROM_TSDB=$(curl -s "$PROM_URL/api/v1/status/tsdb" 2>/dev/null || echo "{}")
if echo "$PROM_TSDB" | grep -q "seriesCountByMetricName"; then
    print_status 0 "Prometheus TSDB is active"
    
    # Get sample count
    SAMPLE_COUNT=$(curl -s "$PROM_URL/api/v1/query?query=prometheus_tsdb_head_samples" 2>/dev/null | grep -o '"value":\[[^]]*\]' | grep -o '[0-9]*$' | head -1)
    if [ ! -z "$SAMPLE_COUNT" ]; then
        echo "  Current samples in Prometheus: $SAMPLE_COUNT"
    fi
else
    print_status 1 "Cannot query Prometheus TSDB"
fi

# Check remote write metrics
REMOTE_WRITE_SUCCESS=$(curl -s "$PROM_URL/api/v1/query?query=prometheus_remote_storage_samples_total" 2>/dev/null | grep -o '"value":\[[^]]*\]' | grep -o '[0-9]*$' | head -1)
if [ ! -z "$REMOTE_WRITE_SUCCESS" ] && [ "$REMOTE_WRITE_SUCCESS" -gt 0 ]; then
    print_status 0 "Prometheus has sent samples to remote storage"
    echo "  Total samples sent: $REMOTE_WRITE_SUCCESS"
    PROM_SENDING_OK=0
else
    print_status 1 "Prometheus has NOT sent samples to remote storage (or metric not available)"
    PROM_SENDING_OK=1
fi

# Check for failed samples
REMOTE_WRITE_FAILED=$(curl -s "$PROM_URL/api/v1/query?query=prometheus_remote_storage_samples_failed_total" 2>/dev/null | grep -o '"value":\[[^]]*\]' | grep -o '[0-9]*$' | head -1)
if [ ! -z "$REMOTE_WRITE_FAILED" ]; then
    if [ "$REMOTE_WRITE_FAILED" -eq 0 ]; then
        print_status 0 "No failed remote write samples"
    else
        print_status 1 "Remote write has $REMOTE_WRITE_FAILED failed samples"
    fi
fi

echo ""
echo "Step 4: Check Mimir Data Ingestion"
echo "-----------------------------------"

# Check if Mimir is receiving data
MIMIR_SAMPLES=$(curl -s "$MIMIR_URL/prometheus/api/v1/query?query=cortex_ingester_ingested_samples_total" 2>/dev/null | grep -o '"value":\[[^]]*\]' | grep -o '[0-9]*$' | head -1)
if [ ! -z "$MIMIR_SAMPLES" ] && [ "$MIMIR_SAMPLES" -gt 0 ]; then
    print_status 0 "Mimir is receiving samples"
    echo "  Total samples ingested: $MIMIR_SAMPLES"
    MIMIR_INGESTING_OK=0
else
    print_status 1 "Mimir is NOT receiving samples (or metric not available)"
    MIMIR_INGESTING_OK=1
fi

# Check active series in Mimir
MIMIR_SERIES=$(curl -s "$MIMIR_URL/prometheus/api/v1/query?query=cortex_ingester_active_series" 2>/dev/null | grep -o '"value":\[[^]]*\]' | grep -o '[0-9]*$' | head -1)
if [ ! -z "$MIMIR_SERIES" ] && [ "$MIMIR_SERIES" -gt 0 ]; then
    print_status 0 "Mimir has active time series"
    echo "  Active series: $MIMIR_SERIES"
else
    print_status 1 "Mimir has NO active series"
fi

# Try to query a common metric from Mimir
TEST_QUERY=$(curl -s "$MIMIR_URL/prometheus/api/v1/query?query=up" 2>/dev/null)
if echo "$TEST_QUERY" | grep -q '"status":"success"'; then
    RESULT_COUNT=$(echo "$TEST_QUERY" | grep -o '"result":\[.*\]' | grep -c '"metric"' || echo "0")
    if [ "$RESULT_COUNT" -gt 0 ]; then
        print_status 0 "Mimir can query metrics (found $RESULT_COUNT 'up' series)"
        MIMIR_QUERY_OK=0
    else
        print_status 1 "Mimir query succeeded but no data found"
        MIMIR_QUERY_OK=1
    fi
else
    print_status 1 "Cannot query metrics from Mimir"
    MIMIR_QUERY_OK=1
fi

echo ""
echo "Step 5: Check Grafana → Mimir Connection"
echo "-----------------------------------------"

# Check if Grafana has Mimir datasource
GRAFANA_DS=$(curl -s "$GRAFANA_URL/api/datasources" 2>/dev/null || echo "[]")
if echo "$GRAFANA_DS" | grep -q '"name":"Mimir"'; then
    print_status 0 "Grafana has Mimir datasource configured"
    
    # Extract Mimir datasource ID
    MIMIR_DS_ID=$(echo "$GRAFANA_DS" | grep -o '"id":[0-9]*,"uid":"grafana_mimir"' | grep -o '[0-9]*' | head -1)
    if [ ! -z "$MIMIR_DS_ID" ]; then
        echo "  Mimir datasource ID: $MIMIR_DS_ID"
        
        # Get datasource URL
        MIMIR_DS_URL=$(echo "$GRAFANA_DS" | grep -A 10 '"name":"Mimir"' | grep -o '"url":"[^"]*"' | head -1 | cut -d'"' -f4)
        echo "  Mimir datasource URL: $MIMIR_DS_URL"
        
        # Check if using internal link
        if echo "$MIMIR_DS_URL" | grep -q "railway.internal"; then
            print_status 0 "Grafana using Railway internal network for Mimir ✓"
            GRAFANA_MIMIR_URL_OK=0
        else
            print_status 1 "Grafana NOT using Railway internal network for Mimir"
            GRAFANA_MIMIR_URL_OK=1
        fi
    fi
    GRAFANA_DS_OK=0
else
    print_status 1 "Grafana does NOT have Mimir datasource configured"
    GRAFANA_DS_OK=1
fi

# Test Grafana → Mimir query
if [ ! -z "$MIMIR_DS_ID" ]; then
    GRAFANA_QUERY=$(curl -s -X POST "$GRAFANA_URL/api/ds/query" \
        -H "Content-Type: application/json" \
        -d "{\"queries\":[{\"datasource\":{\"uid\":\"grafana_mimir\"},\"expr\":\"up\",\"refId\":\"A\"}]}" 2>/dev/null)
    
    if echo "$GRAFANA_QUERY" | grep -q '"status":"success"'; then
        print_status 0 "Grafana can query data from Mimir"
        GRAFANA_QUERY_OK=0
    else
        print_status 1 "Grafana CANNOT query data from Mimir"
        GRAFANA_QUERY_OK=1
    fi
fi

echo ""
echo "=================================================="
echo "Summary Report"
echo "=================================================="
echo ""

# Overall status
TOTAL_CHECKS=11
PASSED_CHECKS=0

[ $PROM_OK -eq 0 ] && ((PASSED_CHECKS++))
[ $MIMIR_OK -eq 0 ] && ((PASSED_CHECKS++))
[ $GRAFANA_OK -eq 0 ] && ((PASSED_CHECKS++))
[ $PROM_REMOTE_WRITE_OK -eq 0 ] && ((PASSED_CHECKS++))
[ $PROM_SENDING_OK -eq 0 ] && ((PASSED_CHECKS++))
[ $MIMIR_INGESTING_OK -eq 0 ] && ((PASSED_CHECKS++))
[ $MIMIR_QUERY_OK -eq 0 ] && ((PASSED_CHECKS++))
[ $GRAFANA_DS_OK -eq 0 ] && ((PASSED_CHECKS++))
[ $GRAFANA_MIMIR_URL_OK -eq 0 ] && ((PASSED_CHECKS++))
[ $GRAFANA_QUERY_OK -eq 0 ] && ((PASSED_CHECKS++))

echo "Checks passed: $PASSED_CHECKS / $TOTAL_CHECKS"
echo ""

# Data flow status
echo "Data Flow Status:"
echo "┌─────────────┐    remote_write    ┌──────┐    query    ┌─────────┐"
echo "│ Prometheus  │ ──────────────────> │ Mimir│ <────────── │ Grafana │"
echo "└─────────────┘                     └──────┘             └─────────┘"
echo ""

if [ $PROM_OK -eq 0 ] && [ $PROM_SENDING_OK -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Prometheus → Mimir: Data flowing"
else
    echo -e "${RED}✗${NC} Prometheus → Mimir: NOT working"
fi

if [ $MIMIR_OK -eq 0 ] && [ $MIMIR_INGESTING_OK -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Mimir: Receiving and storing data"
else
    echo -e "${RED}✗${NC} Mimir: NOT receiving data"
fi

if [ $GRAFANA_OK -eq 0 ] && [ $GRAFANA_QUERY_OK -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Grafana → Mimir: Can query data"
else
    echo -e "${RED}✗${NC} Grafana → Mimir: Cannot query data"
fi

echo ""
echo "=================================================="
echo "Recommendations"
echo "=================================================="
echo ""

if [ $PROM_REMOTE_WRITE_OK -ne 0 ]; then
    echo -e "${YELLOW}⚠${NC} Prometheus remote_write not configured for Mimir"
    echo "  Action: Add RAILWAY_ENVIRONMENT=production to Prometheus service"
    echo ""
fi

if [ $PROM_SENDING_OK -ne 0 ]; then
    echo -e "${YELLOW}⚠${NC} Prometheus not sending samples to Mimir"
    echo "  Check: Prometheus logs for remote write errors"
    echo "  Check: Mimir is accessible from Prometheus"
    echo ""
fi

if [ $MIMIR_INGESTING_OK -ne 0 ]; then
    echo -e "${YELLOW}⚠${NC} Mimir not ingesting samples"
    echo "  Check: Mimir logs for ingestion errors"
    echo "  Check: Mimir configuration (kvstore, rings)"
    echo ""
fi

if [ $GRAFANA_MIMIR_URL_OK -ne 0 ]; then
    echo -e "${YELLOW}⚠${NC} Grafana not using Railway internal network for Mimir"
    echo "  Action: Set MIMIR_INTERNAL_URL=http://mimir.railway.internal:9009 for Grafana"
    echo ""
fi

if [ $GRAFANA_QUERY_OK -ne 0 ]; then
    echo -e "${YELLOW}⚠${NC} Grafana cannot query Mimir"
    echo "  Check: Mimir datasource configuration in Grafana"
    echo "  Check: Network connectivity between Grafana and Mimir"
    echo ""
fi

# Overall health
echo ""
if [ $PASSED_CHECKS -eq $TOTAL_CHECKS ]; then
    echo -e "${GREEN}🎉 All checks passed! The data flow is working correctly.${NC}"
    exit 0
elif [ $PASSED_CHECKS -ge 7 ]; then
    echo -e "${YELLOW}⚠ Most checks passed. Minor issues detected.${NC}"
    exit 1
else
    echo -e "${RED}❌ Multiple issues detected. Review recommendations above.${NC}"
    exit 2
fi
