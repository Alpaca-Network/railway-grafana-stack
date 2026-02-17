#!/bin/sh
set -e

echo "=== Tempo Startup ==="

# ============================================================
# Mimir Remote Write Configuration
# Tempo's metrics_generator sends span metrics to Mimir
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

# Substitute the Mimir URL in tempo.yml
if [ -f "/etc/tempo/tempo.yml" ]; then
    sed -i "s|MIMIR_REMOTE_WRITE_URL|${MIMIR_REMOTE_WRITE_URL}|g" /etc/tempo/tempo.yml
    echo "Configured metrics_generator remote_write to: $MIMIR_REMOTE_WRITE_URL"
fi

# Clean up any corrupted data in /var/tempo
# The "wal" tenant error means there's a directory named "wal" being treated as a tenant
if [ -d "/var/tempo" ]; then
    echo "Checking for corrupted tenant directories..."
    
    # Remove any "wal" directory that's at the traces level (wrong location)
    if [ -d "/var/tempo/traces/wal" ]; then
        echo "Found misplaced 'wal' directory in traces. Removing..."
        rm -rf /var/tempo/traces/wal
    fi
    
    # Check for directories with invalid names in traces folder
    for dir in /var/tempo/traces/*/; do
        if [ -d "$dir" ]; then
            dirname=$(basename "$dir")
            # Skip valid tenant names (single-tenant, generator, etc.)
            case "$dirname" in
                single-tenant|generator|traces|wal)
                    # "wal" shouldn't be here - remove it
                    if [ "$dirname" = "wal" ]; then
                        echo "Removing invalid 'wal' tenant directory..."
                        rm -rf "$dir"
                    fi
                    ;;
            esac
        fi
    done
    
    # Clean WAL directory of any non-UUID entries
    if [ -d "/var/tempo/wal" ]; then
        echo "Cleaning WAL directory..."
        for entry in /var/tempo/wal/*; do
            if [ -e "$entry" ]; then
                name=$(basename "$entry")
                # Check if it's a valid UUID or known file
                if ! echo "$name" | grep -qE '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'; then
                    if [ "$name" != "blocks" ]; then
                        echo "Removing invalid WAL entry: $name"
                        rm -rf "$entry"
                    fi
                fi
            fi
        done
    fi
fi

# Ensure directories exist with correct permissions
# IMPORTANT: /var/tempo/generator/* directories are required for metrics_generator
mkdir -p /var/tempo/traces /var/tempo/wal /var/tempo/generator/wal /var/tempo/generator/traces
chmod -R 777 /var/tempo || true

echo "Created directories:"
ls -la /var/tempo/

echo "Starting Tempo..."
exec /tempo -config.file=/etc/tempo/tempo.yml "$@"
