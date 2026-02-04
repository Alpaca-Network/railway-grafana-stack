#!/bin/sh
set -e

echo "==========================================="
echo "Tempo Startup - Transparent Telemetry Ingestion"
echo "==========================================="

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
    echo "✅ Configured metrics_generator remote_write to: $MIMIR_REMOTE_WRITE_URL"
else
    echo "❌ ERROR: /etc/tempo/tempo.yml not found!"
    exit 1
fi

# ============================================================
# Configuration Validation
# ============================================================

echo ""
echo "Validating Tempo configuration..."

# Check that MIMIR_REMOTE_WRITE_URL was substituted
if grep -q "MIMIR_REMOTE_WRITE_URL" /etc/tempo/tempo.yml; then
    echo "❌ ERROR: MIMIR_REMOTE_WRITE_URL placeholder not replaced in config!"
    exit 1
else
    echo "✅ MIMIR_REMOTE_WRITE_URL successfully substituted"
fi

# Display key configuration sections
echo ""
echo "Key Configuration:"
echo "-------------------"
echo "OTLP Endpoints:"
echo "  - gRPC: 0.0.0.0:4317"
echo "  - HTTP: 0.0.0.0:4318"
echo ""
echo "Span Metrics Dimensions:"
grep -A 15 "dimensions:" /etc/tempo/tempo.yml | head -20 | sed 's/^/  /'
echo ""
echo "Histogram Buckets:"
grep "histogram_buckets:" /etc/tempo/tempo.yml | sed 's/^/  /'
echo ""

# ============================================================
# Trace Attribute Monitoring Setup
# ============================================================

echo "Trace Attribute Validation:"
echo "---------------------------"
echo "Required attributes for transparent ingestion:"
echo "  ✓ service.name"
echo "  ✓ gen_ai.system"
echo "  ✓ gen_ai.request.model"
echo "  ✓ gen_ai.operation.name"
echo "  ✓ http.response.status_code"
echo ""
echo "These attributes will be extracted as metric labels."
echo "Missing attributes will result in empty label values."
echo ""
echo "Monitor these Tempo metrics to validate ingestion:"
echo "  - tempo_distributor_spans_received_total"
echo "  - tempo_metrics_generator_spans_processed_total"
echo "  - tempo_metrics_generator_spans_discarded_total"
echo "  - traces_spanmetrics_calls_total (generated span metrics)"
echo ""

# ============================================================
# Directory Setup and Cleanup
# ============================================================

echo "Directory Setup:"
echo "----------------"

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
chmod -R 777 /var/tempo

echo "✅ Created required directories:"
ls -la /var/tempo/

# ============================================================
# Mimir Connectivity Test
# ============================================================

echo ""
echo "Testing Mimir Connectivity:"
echo "---------------------------"
# Extract hostname from URL
MIMIR_HOST=$(echo "$MIMIR_REMOTE_WRITE_URL" | sed 's|http://||' | sed 's|/.*||')

# Try to reach Mimir (5 attempts with 2 second delay)
MIMIR_READY=false
for i in 1 2 3 4 5; do
    if wget -qO- "http://${MIMIR_HOST}/ready" 2>/dev/null | grep -q "ready"; then
        echo "✅ Mimir is ready at: $MIMIR_HOST"
        MIMIR_READY=true
        break
    fi
    echo "⏳ Waiting for Mimir to be ready (attempt $i/5)..."
    sleep 2
done

if [ "$MIMIR_READY" = "false" ]; then
    echo "⚠️  Mimir not ready yet. Span metrics remote write will retry automatically."
    echo "    This is normal during initial startup. Check Mimir logs if this persists."
fi

# ============================================================
# Start Tempo
# ============================================================

echo ""
echo "==========================================="
echo "Starting Tempo with transparent telemetry ingestion..."
echo "==========================================="
echo "Endpoints:"
echo "  - OTLP gRPC: 0.0.0.0:4317"
echo "  - OTLP HTTP: 0.0.0.0:4318"
echo "  - Query API: 0.0.0.0:3200"
echo ""
echo "Metrics Generator:"
echo "  - Remote Write Target: $MIMIR_REMOTE_WRITE_URL"
echo "  - Generated Metrics: traces_spanmetrics_*"
echo ""
echo "Documentation:"
echo "  - Architecture: /docs/architecture/TRANSPARENT_TELEMETRY_INGESTION.md"
echo "  - Backend Integration: /docs/backend/OTLP_INTEGRATION_GUIDE.md"
echo "==========================================="
echo ""

exec /tempo -config.file=/etc/tempo/tempo.yml "$@"
