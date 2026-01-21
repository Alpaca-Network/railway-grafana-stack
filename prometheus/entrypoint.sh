#!/bin/sh
set -e

# ============================================================
# Prometheus Entrypoint Script
# Substitutes FASTAPI_TARGET and FASTAPI_SCHEME in prom.yml
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

echo "==========================================="
echo "Prometheus Configuration"
echo "==========================================="
echo "FASTAPI_TARGET: $TARGET"
echo "FASTAPI_SCHEME: $SCHEME"
echo "RAILWAY_ENVIRONMENT: ${RAILWAY_ENVIRONMENT:-not set (local mode)}"
echo "==========================================="

# Substitute placeholders in prom.yml
cp /etc/prometheus/prom.yml /tmp/prom.yml.tmp
sed -e "s|FASTAPI_TARGET|${TARGET}|g" \
    -e "s|FASTAPI_SCHEME|${SCHEME}|g" \
    /tmp/prom.yml.tmp > /etc/prometheus/prom.yml

# Show the resulting scrape targets for debugging
echo "Configured scrape targets:"
grep -E "targets:|scheme:" /etc/prometheus/prom.yml | head -20
echo "==========================================="

# Start Prometheus with provided arguments
exec prometheus "$@"
