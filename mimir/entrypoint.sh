#!/bin/sh
set -e

# ============================================================
# Mimir Entrypoint Script
# Starts Mimir with the appropriate configuration
# ============================================================

# Determine config file based on environment
CONFIG_FILE="${CONFIG_FILE:-/etc/mimir/mimir-railway.yml}"

echo "==========================================="
echo "Mimir Startup"
echo "==========================================="
echo "CONFIG_FILE: $CONFIG_FILE"
echo "RAILWAY_ENVIRONMENT: ${RAILWAY_ENVIRONMENT:-not set}"
echo "==========================================="

# Verify config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Config file not found: $CONFIG_FILE"
    echo "Available configs:"
    ls -la /etc/mimir/ 2>/dev/null || echo "  (directory not found)"
    exit 1
fi

# Ensure data directories exist with proper permissions
echo "Setting up data directories..."
mkdir -p /data/mimir/blocks /data/mimir/tsdb /data/mimir/bucket-sync /data/mimir/compactor
chmod -R 0777 /data/mimir 2>/dev/null || true

# Create activity log file if it doesn't exist
touch /data/mimir/activity.log 2>/dev/null || true

# Show config summary
echo "Config file contents (first 30 lines):"
head -30 "$CONFIG_FILE"
echo "==========================================="

# Find Mimir binary (it could be in different locations)
MIMIR_BIN=""
if command -v mimir >/dev/null 2>&1; then
    MIMIR_BIN="mimir"
elif [ -x "/bin/mimir" ]; then
    MIMIR_BIN="/bin/mimir"
elif [ -x "/usr/bin/mimir" ]; then
    MIMIR_BIN="/usr/bin/mimir"
else
    echo "ERROR: Mimir binary not found!"
    echo "Searching for mimir..."
    find / -name "mimir" -type f 2>/dev/null | head -5
    exit 1
fi

echo "Using Mimir binary: $MIMIR_BIN"
echo "Starting Mimir..."
exec $MIMIR_BIN -config.file="$CONFIG_FILE"
