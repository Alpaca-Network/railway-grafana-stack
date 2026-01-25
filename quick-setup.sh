#!/bin/bash

# ============================================================
# Quick Setup Script: Enable Prometheus → Mimir on Railway
# ============================================================

set -e

echo "=========================================="
echo "Prometheus → Mimir Quick Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Railway CLI is installed
echo -e "${BLUE}Step 1: Checking Railway CLI...${NC}"
if ! command -v railway &> /dev/null; then
    echo -e "${YELLOW}⚠️  Railway CLI not found${NC}"
    echo ""
    echo "To install Railway CLI:"
    echo "  npm install -g @railway/cli"
    echo "  OR"
    echo "  brew install railway"
    echo ""
    echo "After installing, run: railway link"
    echo ""
    echo "Alternative: Use Railway Dashboard manually"
    echo "  See: NEXT_STEPS.md for manual instructions"
    exit 1
else
    RAILWAY_VERSION=$(railway --version)
    echo -e "${GREEN}✓ Railway CLI installed: $RAILWAY_VERSION${NC}"
fi

echo ""

# Check if linked to a project
echo -e "${BLUE}Step 2: Checking Railway project link...${NC}"
if ! railway status &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not linked to a Railway project${NC}"
    echo ""
    echo "Run: railway link"
    echo "Then select your GatewayZ project"
    echo ""
    exit 1
else
    echo -e "${GREEN}✓ Linked to Railway project${NC}"
fi

echo ""

# Check if Prometheus service exists
echo -e "${BLUE}Step 3: Checking Prometheus service...${NC}"
if ! railway service list 2>&1 | grep -q "prometheus"; then
    echo -e "${RED}✗ Prometheus service not found${NC}"
    echo ""
    echo "Make sure you have a Prometheus service deployed on Railway"
    echo ""
    exit 1
else
    echo -e "${GREEN}✓ Prometheus service found${NC}"
fi

echo ""

# Check if Mimir service exists
echo -e "${BLUE}Step 4: Checking Mimir service...${NC}"
if ! railway service list 2>&1 | grep -q "mimir"; then
    echo -e "${RED}✗ Mimir service not found${NC}"
    echo ""
    echo "Make sure you have a Mimir service deployed on Railway"
    echo ""
    exit 1
else
    echo -e "${GREEN}✓ Mimir service found${NC}"
fi

echo ""

# Offer to set the environment variable
echo -e "${BLUE}Step 5: Set RAILWAY_ENVIRONMENT variable${NC}"
echo ""
echo "This script will set the following environment variable on Prometheus service:"
echo "  RAILWAY_ENVIRONMENT=production"
echo ""
echo "This enables Prometheus to use Railway's internal network for Mimir."
echo ""
read -p "Do you want to set this variable now? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BLUE}Setting environment variable...${NC}"
    
    # Note: Railway CLI doesn't have a direct command to set env vars
    # We need to guide the user to do it manually
    echo -e "${YELLOW}⚠️  Railway CLI doesn't support setting variables via command${NC}"
    echo ""
    echo "Please follow these manual steps:"
    echo ""
    echo "1. Go to: https://railway.app/dashboard"
    echo "2. Select your project: GatewayZ (or your project name)"
    echo "3. Click on: Prometheus service"
    echo "4. Click: Variables tab"
    echo "5. Click: + New Variable"
    echo "6. Enter:"
    echo "   - Key: RAILWAY_ENVIRONMENT"
    echo "   - Value: production"
    echo "7. Click: Add"
    echo "8. Wait 2-3 minutes for automatic redeploy"
    echo ""
    echo -e "${GREEN}After setting the variable, press ENTER to continue...${NC}"
    read -r
fi

echo ""

# Offer to check Prometheus logs
echo -e "${BLUE}Step 6: Check Prometheus logs${NC}"
echo ""
echo "This will show the last 100 lines of Prometheus logs."
echo "Look for: MIMIR_URL and RAILWAY_ENVIRONMENT values"
echo ""
read -p "Do you want to check Prometheus logs now? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BLUE}Fetching Prometheus logs...${NC}"
    echo ""
    railway logs --service prometheus --lines 100 | grep -E "MIMIR|RAILWAY|remote_write" || true
    echo ""
fi

echo ""

# Offer to run diagnostic script
echo -e "${BLUE}Step 7: Run diagnostic script${NC}"
echo ""
echo "This will run a comprehensive diagnostic inside the Prometheus container."
echo "It checks:"
echo "  - DNS resolution for mimir.railway.internal"
echo "  - TCP connection to Mimir"
echo "  - HTTP endpoints (/ready, /api/v1/push)"
echo "  - Prometheus configuration"
echo "  - Remote write metrics"
echo ""
read -p "Do you want to run the diagnostic now? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BLUE}Running diagnostic script...${NC}"
    echo ""
    
    # Copy diagnostic script to Prometheus container and run it
    echo "Note: This requires the diagnostic script to be in the Prometheus image"
    echo "If you see 'file not found', the script needs to be added to Dockerfile"
    echo ""
    
    railway run --service prometheus -- bash -c '
        if [ -f /app/diagnose-prometheus-mimir.sh ]; then
            bash /app/diagnose-prometheus-mimir.sh
        else
            echo "Diagnostic script not found in container"
            echo "Running basic checks instead..."
            echo ""
            echo "1. Checking DNS resolution:"
            nslookup mimir.railway.internal || echo "DNS resolution failed"
            echo ""
            echo "2. Checking Mimir health:"
            curl -s http://mimir.railway.internal:9009/ready || echo "Mimir not accessible"
            echo ""
            echo "3. Checking Prometheus config:"
            grep -A5 "remote_write:" /etc/prometheus/prom.yml || true
        fi
    ' || echo -e "${RED}Failed to run diagnostic${NC}"
fi

echo ""

# Final instructions
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Wait 5 minutes for metrics to accumulate"
echo ""
echo "2. Verify Prometheus is sending data:"
echo "   - Visit: https://prometheus-{your-project}.railway.app"
echo "   - Go to: Status → TSDB Status"
echo "   - Check: Remote Write section (Samples Sent > 0)"
echo ""
echo "3. Verify Mimir is receiving data:"
echo "   - On Prometheus UI, run query: cortex_ingester_ingested_samples_total"
echo "   - Should show > 0 samples"
echo ""
echo "4. Test Grafana → Mimir connection:"
echo "   - Visit: https://grafana-{your-project}.railway.app"
echo "   - Go to: Explore"
echo "   - Select: Mimir datasource"
echo "   - Query: up"
echo "   - Should show time series data"
echo ""
echo "If issues persist, check: NEXT_STEPS.md for detailed troubleshooting"
echo ""
echo "=========================================="
