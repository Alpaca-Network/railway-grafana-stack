#!/bin/bash

# ============================================================
# Verify Remote Write Configuration Script
# Checks if Prometheus is actually writing to Mimir
# ============================================================

set -e

echo "=========================================="
echo "Remote Write Verification"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Step 1: Check if remote_write is in the final config
echo -e "${BLUE}Step 1: Checking Prometheus configuration...${NC}"
echo ""

if [ -f /etc/prometheus/prom.yml ]; then
    echo "Found prom.yml, checking remote_write section:"
    echo ""
    
    if grep -q "remote_write:" /etc/prometheus/prom.yml; then
        echo -e "${GREEN}✓ remote_write section found${NC}"
        echo ""
        echo "Full remote_write configuration:"
        grep -A 15 "^remote_write:" /etc/prometheus/prom.yml
        echo ""
        
        # Check if MIMIR_URL placeholder is still there
        if grep -q "MIMIR_URL" /etc/prometheus/prom.yml; then
            echo -e "${RED}✗ CRITICAL: MIMIR_URL placeholder not replaced!${NC}"
            echo "  The entrypoint script failed to substitute the URL"
            echo ""
            echo "Debug info:"
            echo "  RAILWAY_ENVIRONMENT=${RAILWAY_ENVIRONMENT:-not set}"
            echo "  MIMIR_INTERNAL_URL=${MIMIR_INTERNAL_URL:-not set}"
            echo ""
            echo "Expected: url: http://mimir.railway.internal:9009/api/v1/push"
            echo "Actual:   url: MIMIR_URL/api/v1/push"
            exit 1
        else
            echo -e "${GREEN}✓ MIMIR_URL placeholder has been replaced${NC}"
            
            # Extract the actual URL
            ACTUAL_URL=$(grep -A 15 "^remote_write:" /etc/prometheus/prom.yml | grep "url:" | head -1 | awk '{print $3}')
            echo "  Configured URL: $ACTUAL_URL"
            
            if [[ "$ACTUAL_URL" == *"mimir.railway.internal"* ]]; then
                echo -e "${GREEN}✓ Using Railway internal network (correct)${NC}"
            elif [[ "$ACTUAL_URL" == *"mimir:9009"* ]]; then
                echo -e "${YELLOW}⚠ Using Docker Compose hostname (only works locally)${NC}"
            else
                echo -e "${YELLOW}⚠ Using different hostname: $ACTUAL_URL${NC}"
            fi
        fi
    else
        echo -e "${RED}✗ No remote_write section found in config!${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ /etc/prometheus/prom.yml not found${NC}"
    exit 1
fi

echo ""

# Step 2: Check Prometheus metrics for remote_write status
echo -e "${BLUE}Step 2: Checking Prometheus remote_write metrics...${NC}"
echo ""

# Check if Prometheus is running
if ! curl -sf http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo -e "${RED}✗ Prometheus is not healthy${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prometheus is healthy${NC}"
echo ""

# Query remote write metrics
echo "Querying remote_write metrics:"
echo ""

# Total samples sent
SAMPLES_TOTAL=$(curl -sf 'http://localhost:9090/api/v1/query?query=prometheus_remote_storage_samples_total' | grep -o '"value":\[[^]]*\]' | grep -o '[0-9.]*$' || echo "0")
echo "  Total samples sent: $SAMPLES_TOTAL"

# Failed samples
SAMPLES_FAILED=$(curl -sf 'http://localhost:9090/api/v1/query?query=prometheus_remote_storage_samples_failed_total' | grep -o '"value":\[[^]]*\]' | grep -o '[0-9.]*$' || echo "0")
echo "  Failed samples: $SAMPLES_FAILED"

# Pending samples
SAMPLES_PENDING=$(curl -sf 'http://localhost:9090/api/v1/query?query=prometheus_remote_storage_samples_pending' | grep -o '"value":\[[^]]*\]' | grep -o '[0-9.]*$' || echo "0")
echo "  Pending samples: $SAMPLES_PENDING"

# Active shards
SHARDS=$(curl -sf 'http://localhost:9090/api/v1/query?query=prometheus_remote_storage_shards' | grep -o '"value":\[[^]]*\]' | grep -o '[0-9.]*$' || echo "0")
echo "  Active shards: $SHARDS"

echo ""

# Analyze results
if (( $(echo "$SAMPLES_TOTAL > 0" | bc -l) )); then
    echo -e "${GREEN}✓ Prometheus IS sending samples to remote storage${NC}"
    echo "  Rate: $(echo "scale=2; $SAMPLES_TOTAL / 60" | bc) samples/sec (avg over last minute)"
    
    if (( $(echo "$SAMPLES_FAILED > 0" | bc -l) )); then
        echo -e "${YELLOW}⚠ Some samples are failing to write${NC}"
        echo "  Failure rate: $(echo "scale=2; $SAMPLES_FAILED / $SAMPLES_TOTAL * 100" | bc)%"
    else
        echo -e "${GREEN}✓ No failed samples (100% success rate)${NC}"
    fi
else
    echo -e "${RED}✗ Prometheus is NOT sending any samples${NC}"
    echo ""
    echo "Possible causes:"
    echo "  1. remote_write not properly configured"
    echo "  2. No scrape targets configured/active"
    echo "  3. Prometheus just started (wait 30 seconds)"
    echo "  4. Mimir endpoint unreachable"
fi

echo ""

# Step 3: Check scrape targets
echo -e "${BLUE}Step 3: Checking scrape targets...${NC}"
echo ""

TARGETS_UP=$(curl -sf 'http://localhost:9090/api/v1/targets' | grep -o '"health":"up"' | wc -l || echo "0")
TARGETS_DOWN=$(curl -sf 'http://localhost:9090/api/v1/targets' | grep -o '"health":"down"' | wc -l || echo "0")
TARGETS_TOTAL=$((TARGETS_UP + TARGETS_DOWN))

echo "  Total targets: $TARGETS_TOTAL"
echo "  Targets UP: $TARGETS_UP"
echo "  Targets DOWN: $TARGETS_DOWN"

if [ "$TARGETS_UP" -gt 0 ]; then
    echo -e "${GREEN}✓ At least one target is UP and being scraped${NC}"
else
    echo -e "${RED}✗ No targets are UP - Prometheus has no data to send!${NC}"
    echo ""
    echo "Check target status: http://localhost:9090/targets"
fi

echo ""

# Step 4: Test Mimir endpoint
echo -e "${BLUE}Step 4: Testing Mimir endpoint...${NC}"
echo ""

# Extract Mimir URL from config
MIMIR_URL=$(grep -A 15 "^remote_write:" /etc/prometheus/prom.yml | grep "url:" | head -1 | awk '{print $3}' | sed 's|/api/v1/push||')

echo "  Mimir base URL: $MIMIR_URL"
echo ""

# Test /ready endpoint
echo "Testing $MIMIR_URL/ready ..."
if curl -sf "$MIMIR_URL/ready" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Mimir /ready endpoint is accessible${NC}"
else
    echo -e "${RED}✗ Mimir /ready endpoint is NOT accessible${NC}"
    echo "  This explains why remote_write isn't working!"
    echo ""
    echo "Debug steps:"
    echo "  1. Check Mimir is running: railway logs --service mimir"
    echo "  2. Test DNS: nslookup mimir.railway.internal"
    echo "  3. Test connectivity: curl -v $MIMIR_URL/ready"
fi

echo ""

# Test /api/v1/push endpoint (just check if it responds, don't actually write)
echo "Testing $MIMIR_URL/api/v1/push ..."
PUSH_RESPONSE=$(curl -sf -X POST "$MIMIR_URL/api/v1/push" 2>&1 || echo "failed")

if [[ "$PUSH_RESPONSE" == *"failed"* ]] || [[ "$PUSH_RESPONSE" == *"Connection refused"* ]]; then
    echo -e "${RED}✗ Mimir /api/v1/push endpoint is NOT accessible${NC}"
    echo "  Error: $PUSH_RESPONSE"
else
    echo -e "${GREEN}✓ Mimir /api/v1/push endpoint is accessible${NC}"
    echo "  (Empty POST returns error, which is expected)"
fi

echo ""

# Step 5: Check for errors in Prometheus logs
echo -e "${BLUE}Step 5: Checking for remote_write errors in logs...${NC}"
echo ""

echo "Recent remote_write related log entries:"
echo ""

# This would need to be run with access to Prometheus logs
# For now, we'll provide instructions
echo "To check Prometheus logs for remote_write errors, run:"
echo "  railway logs --service prometheus | grep -i 'remote.*write\\|mimir\\|error.*send'"
echo ""

# Summary
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo ""

if (( $(echo "$SAMPLES_TOTAL > 0" | bc -l) )) && [ "$TARGETS_UP" -gt 0 ] && curl -sf "$MIMIR_URL/ready" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Remote write is WORKING${NC}"
    echo ""
    echo "  • Prometheus is scraping targets"
    echo "  • Samples are being sent to Mimir"
    echo "  • Mimir is accessible and healthy"
    echo ""
    echo "Next: Check Mimir logs to confirm ingestion"
    echo "  railway logs --service mimir | grep -i 'ingester\\|samples'"
elif (( $(echo "$SAMPLES_TOTAL == 0" | bc -l) )) && [ "$TARGETS_UP" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Configuration looks OK, but no data flowing yet${NC}"
    echo ""
    echo "Possible causes:"
    echo "  1. Prometheus just started (wait 30 seconds)"
    echo "  2. Mimir endpoint not accessible"
    echo "  3. Network connectivity issue"
    echo ""
    echo "Wait 30 seconds and run this script again"
elif [ "$TARGETS_UP" -eq 0 ]; then
    echo -e "${RED}❌ No scrape targets are active${NC}"
    echo ""
    echo "Prometheus has no data to send to Mimir!"
    echo ""
    echo "Fix:"
    echo "  1. Check target configuration in prom.yml"
    echo "  2. Verify target URLs are accessible"
    echo "  3. Check bearer tokens are correct"
    echo "  4. Visit: http://localhost:9090/targets"
else
    echo -e "${RED}❌ Remote write is NOT working${NC}"
    echo ""
    echo "Issues found:"
    if ! curl -sf "$MIMIR_URL/ready" > /dev/null 2>&1; then
        echo "  • Mimir endpoint not accessible"
    fi
    if (( $(echo "$SAMPLES_TOTAL == 0" | bc -l) )); then
        echo "  • No samples being sent"
    fi
    if (( $(echo "$SAMPLES_FAILED > 0" | bc -l) )); then
        echo "  • Some samples are failing"
    fi
    echo ""
    echo "Check the detailed output above for specific issues"
fi

echo ""
echo "=========================================="
