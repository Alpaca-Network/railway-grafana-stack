#!/bin/sh
set -e

echo "=== Loki Startup ==="

# ============================================================
# Mimir Remote Write Configuration
# Loki's ruler sends log-derived metrics to Mimir
# Pattern matches Tempo's metrics_generator -> Mimir remote_write
# ============================================================

if [ -n "$MIMIR_INTERNAL_URL" ]; then
    # Use explicitly set MIMIR_INTERNAL_URL (from Railway env vars)
    MIMIR_REMOTE_WRITE_URL="${MIMIR_INTERNAL_URL}/api/v1/push"
elif [ -n "$RAILWAY_ENVIRONMENT" ]; then
    # Railway production environment - use internal network
    MIMIR_REMOTE_WRITE_URL="http://mimir.railway.internal:9009/api/v1/push"
else
    # Local Docker Compose environment - use Docker service name
    MIMIR_REMOTE_WRITE_URL="http://mimir:9009/api/v1/push"
fi

echo "MIMIR_REMOTE_WRITE_URL: $MIMIR_REMOTE_WRITE_URL"

# Substitute the Mimir URL placeholder in loki-config.yaml
CONFIG_FILE="/etc/loki/loki-config.yaml"
if [ -f "$CONFIG_FILE" ]; then
    sed -i "s|MIMIR_REMOTE_WRITE_URL|${MIMIR_REMOTE_WRITE_URL}|g" "$CONFIG_FILE"
    echo "Configured ruler remote_write to: $MIMIR_REMOTE_WRITE_URL"
fi

# Ensure ruler rules directory exists
# Loki with auth_enabled: false uses tenant "fake"
mkdir -p /loki/rules/fake
chmod -R 0777 /loki/rules 2>/dev/null || true

# Copy rule files into the tenant directory if they exist in the mounted path
if [ -d "/etc/loki/rules" ]; then
    cp /etc/loki/rules/*.yml /loki/rules/fake/ 2>/dev/null || true
    echo "Copied rule files to /loki/rules/fake/"
    ls -la /loki/rules/fake/
fi

# Ensure data directories exist
mkdir -p /loki/chunks /loki/tsdb-index /loki/tsdb-cache /loki/compactor /loki/ruler-wal
chmod -R 0777 /loki 2>/dev/null || true

echo "Testing Mimir connectivity..."
MIMIR_BASE=$(echo "$MIMIR_REMOTE_WRITE_URL" | sed 's|/api/v1/push||')
MIMIR_READY=false
for i in 1 2 3 4 5; do
    if wget -qO- "${MIMIR_BASE}/ready" 2>/dev/null | grep -q "ready"; then
        echo "  Mimir is ready at ${MIMIR_BASE}"
        MIMIR_READY=true
        break
    fi
    echo "  Waiting for Mimir (attempt $i/5)..."
    sleep 2
done
if [ "$MIMIR_READY" = "false" ]; then
    echo "  Mimir not ready yet. Ruler remote_write will retry automatically."
fi

echo "Starting Loki..."
exec loki -config.file="$CONFIG_FILE" "$@"
