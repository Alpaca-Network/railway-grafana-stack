#!/bin/sh
set -e

# ============================================================
# Prometheus Entrypoint Script
# Substitutes environment-specific values in prom.yml:
# - FASTAPI_TARGET, FASTAPI_SCHEME (backend API)
# - MIMIR_URL, MIMIR_TARGET (long-term metrics storage)
# ============================================================

# Determine target and scheme based on environment
# Priority: Environment vars > RAILWAY_ENVIRONMENT detection > local defaults

if [ -n "$FASTAPI_TARGET" ]; then
    # Use explicitly set FASTAPI_TARGET (from docker-compose or Railway env vars)
    TARGET="$FASTAPI_TARGET"

    # Auto-detect scheme based on target
    case "$TARGET" in
        api.gatewayz.ai*|*.railway.app*|*.up.railway.app*)
            SCHEME="${FASTAPI_SCHEME:-https}"
            ;;
        *)
            SCHEME="${FASTAPI_SCHEME:-http}"
            ;;
    esac
elif [ -n "$RAILWAY_ENVIRONMENT" ]; then
    # Railway production environment - use internal network
    TARGET="fastapi-app.railway.internal:8000"
    SCHEME="http"
else
    # Local Docker Compose environment - connect to host
    # Use host.docker.internal for Mac/Windows
    TARGET="host.docker.internal:8000"
    SCHEME="http"
fi

# ============================================================
# Mimir Configuration
# Determines Mimir URL based on environment
# ============================================================

if [ -n "$MIMIR_INTERNAL_URL" ]; then
    # Use explicitly set MIMIR_INTERNAL_URL (from Railway env vars)
    MIMIR_URL="$MIMIR_INTERNAL_URL"
    MIMIR_TARGET=$(echo "$MIMIR_URL" | sed 's|http://||')
elif [ -n "$RAILWAY_ENVIRONMENT" ]; then
    # Railway production environment - use internal network
    # This uses Railway's private networking for faster, more reliable connections
    MIMIR_URL="http://mimir.railway.internal:9009"
    MIMIR_TARGET="mimir.railway.internal:9009"
else
    # Local Docker Compose environment - use Docker service name
    MIMIR_URL="http://mimir:9009"
    MIMIR_TARGET="mimir:9009"
fi

echo "==========================================="
echo "Prometheus Configuration"
echo "==========================================="
echo "FASTAPI_TARGET: $TARGET"
echo "FASTAPI_SCHEME: $SCHEME"
echo "MIMIR_URL: $MIMIR_URL"
echo "MIMIR_TARGET: $MIMIR_TARGET"
echo "RAILWAY_ENVIRONMENT: ${RAILWAY_ENVIRONMENT:-not set (local mode)}"
echo "==========================================="

# Substitute placeholders in prom.yml
cp /etc/prometheus/prom.yml /tmp/prom.yml.tmp
sed -e "s|FASTAPI_TARGET|${TARGET}|g" \
    -e "s|FASTAPI_SCHEME|${SCHEME}|g" \
    -e "s|MIMIR_URL|${MIMIR_URL}|g" \
    -e "s|MIMIR_TARGET|${MIMIR_TARGET}|g" \
    /tmp/prom.yml.tmp > /etc/prometheus/prom.yml

# Show the resulting scrape targets and remote_write for debugging
echo "Configured scrape targets:"
grep -E "targets:|scheme:" /etc/prometheus/prom.yml | head -20
echo ""
echo "Configured remote_write:"
grep -A 10 "^remote_write:" /etc/prometheus/prom.yml
echo ""
echo "Verifying MIMIR_URL substitution:"
if grep -q "MIMIR_URL" /etc/prometheus/prom.yml; then
    echo "  ❌ ERROR: MIMIR_URL placeholder NOT replaced!"
    echo "  This means remote_write will NOT work!"
else
    echo "  ✅ MIMIR_URL placeholder successfully replaced"
fi
echo "==========================================="

# Start Prometheus with provided arguments
exec prometheus "$@"
