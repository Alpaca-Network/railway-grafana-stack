#!/bin/bash
# Diagnose Prometheus → Mimir connection issues
# Run this from the Prometheus container/service on Railway

set -e

echo "========================================"
echo "Prometheus → Mimir Connection Diagnostic"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Step 1: Environment Variables${NC}"
echo "----------------------------------------"
echo "RAILWAY_ENVIRONMENT: ${RAILWAY_ENVIRONMENT:-NOT SET}"
echo "MIMIR_INTERNAL_URL: ${MIMIR_INTERNAL_URL:-NOT SET}"
echo ""

if [ -z "$RAILWAY_ENVIRONMENT" ] && [ -z "$MIMIR_INTERNAL_URL" ]; then
    echo -e "${RED}⚠ WARNING: Neither RAILWAY_ENVIRONMENT nor MIMIR_INTERNAL_URL is set!${NC}"
    echo -e "${YELLOW}Prometheus will use Docker Compose defaults (http://mimir:9009)${NC}"
    echo -e "${YELLOW}This will NOT work on Railway!${NC}"
    echo ""
    echo "FIX: Add one of these to Prometheus service variables in Railway:"
    echo "  Option 1: RAILWAY_ENVIRONMENT=production"
    echo "  Option 2: MIMIR_INTERNAL_URL=http://mimir.railway.internal:9009"
    echo ""
fi

echo -e "${BLUE}Step 2: Prometheus Configuration${NC}"
echo "----------------------------------------"

# Check if prom.yml exists
if [ ! -f "/etc/prometheus/prometheus.yml" ]; then
    echo -e "${RED}✗ prometheus.yml not found at /etc/prometheus/prometheus.yml${NC}"
    exit 1
fi

# Check remote_write configuration
REMOTE_WRITE_URL=$(grep -A5 "remote_write:" /etc/prometheus/prometheus.yml | grep "url:" | head -1 | awk '{print $3}')
if [ -z "$REMOTE_WRITE_URL" ]; then
    echo -e "${RED}✗ No remote_write URL found in configuration${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Remote write URL: $REMOTE_WRITE_URL${NC}"
    
    # Check if using Railway internal network
    if echo "$REMOTE_WRITE_URL" | grep -q "railway.internal"; then
        echo -e "${GREEN}✓ Using Railway internal network${NC}"
    elif echo "$REMOTE_WRITE_URL" | grep -q "mimir:9009"; then
        echo -e "${YELLOW}⚠ Using Docker service name (mimir:9009)${NC}"
        echo -e "${YELLOW}  This won't work on Railway! Set RAILWAY_ENVIRONMENT=production${NC}"
    else
        echo -e "${YELLOW}⚠ Using URL: $REMOTE_WRITE_URL${NC}"
    fi
fi

# Check scrape target for Mimir
MIMIR_TARGET=$(grep -A3 "job_name: 'mimir'" /etc/prometheus/prometheus.yml | grep "targets:" | head -1 | grep -o '\[.*\]')
if [ ! -z "$MIMIR_TARGET" ]; then
    echo -e "${GREEN}✓ Mimir scrape target: $MIMIR_TARGET${NC}"
else
    echo -e "${YELLOW}⚠ No Mimir scrape target found${NC}"
fi

echo ""
echo -e "${BLUE}Step 3: Network Connectivity Tests${NC}"
echo "----------------------------------------"

# Determine Mimir endpoint to test
if [ -n "$MIMIR_INTERNAL_URL" ]; then
    MIMIR_ENDPOINT="$MIMIR_INTERNAL_URL"
elif [ -n "$RAILWAY_ENVIRONMENT" ]; then
    MIMIR_ENDPOINT="http://mimir.railway.internal:9009"
else
    MIMIR_ENDPOINT="http://mimir:9009"
fi

echo "Testing endpoint: $MIMIR_ENDPOINT"
echo ""

# Extract host and port
MIMIR_HOST=$(echo "$MIMIR_ENDPOINT" | sed 's|http://||' | sed 's|https://||' | cut -d: -f1)
MIMIR_PORT=$(echo "$MIMIR_ENDPOINT" | grep -o ':[0-9]*' | tr -d ':' || echo "9009")

# Test 1: DNS Resolution
echo "Test 1: DNS Resolution for $MIMIR_HOST"
if command -v nslookup >/dev/null 2>&1; then
    if nslookup "$MIMIR_HOST" >/dev/null 2>&1; then
        MIMIR_IP=$(nslookup "$MIMIR_HOST" | grep -A1 "Name:" | tail -1 | awk '{print $2}' || echo "unknown")
        echo -e "${GREEN}✓ DNS resolves to: $MIMIR_IP${NC}"
    else
        echo -e "${RED}✗ DNS resolution failed for $MIMIR_HOST${NC}"
        echo -e "${RED}  This means Mimir service is not reachable via this hostname${NC}"
        exit 1
    fi
elif command -v dig >/dev/null 2>&1; then
    if dig "$MIMIR_HOST" +short >/dev/null 2>&1; then
        MIMIR_IP=$(dig "$MIMIR_HOST" +short | head -1)
        echo -e "${GREEN}✓ DNS resolves to: $MIMIR_IP${NC}"
    else
        echo -e "${RED}✗ DNS resolution failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ nslookup/dig not available, skipping DNS test${NC}"
fi

echo ""

# Test 2: TCP Connection
echo "Test 2: TCP Connection to $MIMIR_HOST:$MIMIR_PORT"
if timeout 5 bash -c "echo > /dev/tcp/$MIMIR_HOST/$MIMIR_PORT" 2>/dev/null; then
    echo -e "${GREEN}✓ TCP connection successful${NC}"
else
    echo -e "${RED}✗ Cannot establish TCP connection to $MIMIR_HOST:$MIMIR_PORT${NC}"
    echo -e "${RED}  Possible causes:${NC}"
    echo "  - Mimir service is not running"
    echo "  - Mimir is not listening on port $MIMIR_PORT"
    echo "  - Network policy blocking connection"
    echo "  - Services in different Railway projects"
    exit 1
fi

echo ""

# Test 3: HTTP Ready Endpoint
echo "Test 3: Mimir /ready endpoint"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$MIMIR_ENDPOINT/ready" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Mimir is ready (HTTP $HTTP_CODE)${NC}"
elif [ "$HTTP_CODE" = "000" ]; then
    echo -e "${RED}✗ Connection failed (timeout or connection refused)${NC}"
    exit 1
else
    echo -e "${YELLOW}⚠ Mimir responded with HTTP $HTTP_CODE${NC}"
fi

echo ""

# Test 4: Push API Endpoint
echo "Test 4: Mimir /api/v1/push endpoint (test push)"
PUSH_URL="$MIMIR_ENDPOINT/api/v1/push"
PUSH_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 -X POST "$PUSH_URL" 2>/dev/null || echo "000")

if [ "$PUSH_CODE" = "200" ] || [ "$PUSH_CODE" = "204" ]; then
    echo -e "${GREEN}✓ Push endpoint accessible (HTTP $PUSH_CODE)${NC}"
elif [ "$PUSH_CODE" = "400" ]; then
    echo -e "${GREEN}✓ Push endpoint accessible (HTTP $PUSH_CODE - empty body rejected, which is expected)${NC}"
elif [ "$PUSH_CODE" = "404" ]; then
    echo -e "${RED}✗ Push endpoint returns 404 - Mimir not configured correctly${NC}"
    exit 1
elif [ "$PUSH_CODE" = "000" ]; then
    echo -e "${RED}✗ Cannot reach push endpoint (timeout or connection refused)${NC}"
    exit 1
else
    echo -e "${YELLOW}⚠ Push endpoint responded with HTTP $PUSH_CODE${NC}"
fi

echo ""

# Test 5: Query API Endpoint
echo "Test 5: Mimir /prometheus/api/v1/query endpoint"
QUERY_URL="$MIMIR_ENDPOINT/prometheus/api/v1/query?query=up"
QUERY_RESPONSE=$(curl -s --max-time 5 "$QUERY_URL" 2>/dev/null || echo "{}")

if echo "$QUERY_RESPONSE" | grep -q '"status":"success"'; then
    echo -e "${GREEN}✓ Query endpoint accessible and responding${NC}"
    
    # Check if there's any data
    RESULT_COUNT=$(echo "$QUERY_RESPONSE" | grep -o '"result":\[.*\]' | grep -c '"metric"' || echo "0")
    if [ "$RESULT_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓ Mimir has data ($RESULT_COUNT series found)${NC}"
    else
        echo -e "${YELLOW}⚠ Mimir is working but has no data yet${NC}"
        echo "  This is normal if Prometheus just started sending"
    fi
elif echo "$QUERY_RESPONSE" | grep -q "error"; then
    echo -e "${YELLOW}⚠ Query endpoint responded with error${NC}"
    echo "  Response: $QUERY_RESPONSE"
else
    echo -e "${RED}✗ Query endpoint not responding correctly${NC}"
fi

echo ""
echo -e "${BLUE}Step 4: Prometheus Remote Write Status${NC}"
echo "----------------------------------------"

# Check if Prometheus is running
if ! pgrep -x prometheus >/dev/null; then
    echo -e "${YELLOW}⚠ Prometheus process not running (or ps not available)${NC}"
else
    echo -e "${GREEN}✓ Prometheus process is running${NC}"
fi

# Try to query Prometheus metrics about remote write
PROM_URL="http://localhost:9090"

echo "Querying Prometheus remote write metrics..."
echo ""

# Check remote write samples sent
SAMPLES_SENT=$(curl -s "$PROM_URL/api/v1/query?query=prometheus_remote_storage_samples_total" 2>/dev/null | grep -o '"value":\[[^]]*\]' | grep -o '[0-9]*$' | head -1)
if [ ! -z "$SAMPLES_SENT" ] && [ "$SAMPLES_SENT" -gt 0 ]; then
    echo -e "${GREEN}✓ Prometheus has sent $SAMPLES_SENT samples to remote storage${NC}"
else
    echo -e "${YELLOW}⚠ No remote write samples sent yet (or metric not available)${NC}"
    echo "  Prometheus may have just started, or remote write is not working"
fi

# Check remote write failures
SAMPLES_FAILED=$(curl -s "$PROM_URL/api/v1/query?query=prometheus_remote_storage_samples_failed_total" 2>/dev/null | grep -o '"value":\[[^]]*\]' | grep -o '[0-9]*$' | head -1)
if [ ! -z "$SAMPLES_FAILED" ]; then
    if [ "$SAMPLES_FAILED" -eq 0 ]; then
        echo -e "${GREEN}✓ No failed remote write attempts${NC}"
    else
        echo -e "${RED}✗ $SAMPLES_FAILED samples failed to send${NC}"
        echo -e "${RED}  Check Prometheus logs for remote write errors${NC}"
    fi
fi

# Check current queue size
QUEUE_SIZE=$(curl -s "$PROM_URL/api/v1/query?query=prometheus_remote_storage_samples_pending" 2>/dev/null | grep -o '"value":\[[^]]*\]' | grep -o '[0-9]*$' | head -1)
if [ ! -z "$QUEUE_SIZE" ]; then
    if [ "$QUEUE_SIZE" -lt 1000 ]; then
        echo -e "${GREEN}✓ Remote write queue: $QUEUE_SIZE samples (healthy)${NC}"
    else
        echo -e "${YELLOW}⚠ Remote write queue: $QUEUE_SIZE samples (high backlog)${NC}"
    fi
fi

echo ""
echo "========================================"
echo "Summary"
echo "========================================"
echo ""

# Determine overall status
ISSUES_FOUND=0

if [ -z "$RAILWAY_ENVIRONMENT" ] && [ -z "$MIMIR_INTERNAL_URL" ]; then
    echo -e "${RED}❌ CRITICAL: Environment variables not set${NC}"
    echo "   Set RAILWAY_ENVIRONMENT=production on Prometheus service"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

if [ "$HTTP_CODE" != "200" ]; then
    echo -e "${RED}❌ CRITICAL: Mimir not responding to health checks${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

if [ "$PUSH_CODE" = "404" ] || [ "$PUSH_CODE" = "000" ]; then
    echo -e "${RED}❌ CRITICAL: Cannot reach Mimir push endpoint${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

if [ ! -z "$SAMPLES_FAILED" ] && [ "$SAMPLES_FAILED" -gt 0 ]; then
    echo -e "${YELLOW}⚠ WARNING: Remote write has failures${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

if [ -z "$SAMPLES_SENT" ] || [ "$SAMPLES_SENT" -eq 0 ]; then
    echo -e "${YELLOW}⚠ INFO: No samples sent to Mimir yet${NC}"
    echo "   This is normal if Prometheus just started"
fi

echo ""

if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✓✓✓ All checks passed! Prometheus → Mimir connection is working${NC}"
    echo ""
    echo "Data flow:"
    echo "  Prometheus → $REMOTE_WRITE_URL ✓"
    echo ""
    echo "If you're not seeing data in Mimir yet:"
    echo "  1. Wait 1-2 minutes for Prometheus to send first batch"
    echo "  2. Check Mimir dashboard for ingestion metrics"
    echo "  3. Query Mimir directly: curl '$MIMIR_ENDPOINT/prometheus/api/v1/query?query=up'"
    exit 0
else
    echo -e "${RED}❌ Found $ISSUES_FOUND issue(s) blocking Prometheus → Mimir connection${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Fix the issues listed above"
    echo "  2. Restart Prometheus service"
    echo "  3. Run this diagnostic script again"
    exit 1
fi
