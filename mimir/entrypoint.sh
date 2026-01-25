#!/bin/sh
set -e

# ============================================================
# Mimir Entrypoint Script
# Starts Mimir with the appropriate configuration
# ============================================================

# Determine config file based on environment
CONFIG_FILE="${CONFIG_FILE:-/etc/mimir/mimir-railway.yml}"

echo "==========================================="
echo "Mimir Configuration"
echo "==========================================="
echo "CONFIG_FILE: $CONFIG_FILE"
echo "RAILWAY_ENVIRONMENT: ${RAILWAY_ENVIRONMENT:-not set}"
echo "==========================================="

# Verify config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Config file not found: $CONFIG_FILE"
    echo "Available configs:"
    ls -la /etc/mimir/
    exit 1
fi

# Show config summary
echo "Config file contents (first 20 lines):"
head -20 "$CONFIG_FILE"
echo "==========================================="

# Create activity log file if it doesn't exist
touch /data/mimir/activity.log 2>/dev/null || true

# Start Mimir
echo "Starting Mimir..."
exec /bin/mimir -config.file="$CONFIG_FILE"
