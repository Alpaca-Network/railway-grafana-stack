#!/bin/sh
set -e

# ============================================================
# Prometheus Entrypoint Script
# Substitutes environment-specific values in prometheus.yml:
# - FASTAPI_TARGET, FASTAPI_SCHEME (backend API)
# - MIMIR_URL, MIMIR_TARGET (long-term metrics storage)
# - ALERTMANAGER_TARGET (alerting)
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

# ============================================================
# Alertmanager Configuration
# Determines Alertmanager target based on environment
# ============================================================

if [ -n "$ALERTMANAGER_INTERNAL_URL" ]; then
    # Use explicitly set ALERTMANAGER_INTERNAL_URL (from Railway env vars)
    ALERTMANAGER_TARGET=$(echo "$ALERTMANAGER_INTERNAL_URL" | sed 's|http://||')
elif [ -n "$RAILWAY_ENVIRONMENT" ]; then
    # Railway production environment - use internal network
    # Note: Alertmanager service must be named 'alertmanager' in Railway
    ALERTMANAGER_TARGET="alertmanager.railway.internal:9093"
else
    # Local Docker Compose environment - use Docker service name
    ALERTMANAGER_TARGET="alertmanager:9093"
fi

# ============================================================
# Redis Exporter Configuration
# Redis Exporter runs in the backend project (separate Railway project)
# So we need to use the public URL, not internal networking
# ============================================================

if [ -n "$REDIS_EXPORTER_URL" ]; then
    # Use explicitly set REDIS_EXPORTER_URL (public URL from backend project)
    # Remove https:// prefix if present for the target
    REDIS_EXPORTER_TARGET=$(echo "$REDIS_EXPORTER_URL" | sed 's|https://||' | sed 's|http://||')
else
    # Default/placeholder - must be set in Railway environment variables
    REDIS_EXPORTER_TARGET="redis-exporter.railway.internal:9121"
    echo "WARNING: REDIS_EXPORTER_URL not set. Redis metrics will not be scraped."
    echo "Set REDIS_EXPORTER_URL to the public URL of your Redis Exporter service."
fi

echo "==========================================="
echo "Prometheus Configuration"
echo "==========================================="
echo "FASTAPI_TARGET: $TARGET"
echo "FASTAPI_SCHEME: $SCHEME"
echo "MIMIR_URL: $MIMIR_URL"
echo "MIMIR_TARGET: $MIMIR_TARGET"
echo "ALERTMANAGER_TARGET: $ALERTMANAGER_TARGET"
echo "REDIS_EXPORTER_TARGET: $REDIS_EXPORTER_TARGET"
echo "RAILWAY_ENVIRONMENT: ${RAILWAY_ENVIRONMENT:-not set (local mode)}"
echo "==========================================="

# Substitute placeholders in prometheus.yml
cp /etc/prometheus/prometheus.yml /tmp/prometheus.yml.tmp
sed -e "s|FASTAPI_TARGET|${TARGET}|g" \
    -e "s|FASTAPI_SCHEME|${SCHEME}|g" \
    -e "s|MIMIR_URL|${MIMIR_URL}|g" \
    -e "s|MIMIR_TARGET|${MIMIR_TARGET}|g" \
    -e "s|ALERTMANAGER_TARGET|${ALERTMANAGER_TARGET}|g" \
    -e "s|REDIS_EXPORTER_TARGET|${REDIS_EXPORTER_TARGET}|g" \
    /tmp/prometheus.yml.tmp > /etc/prometheus/prometheus.yml

# Show the resulting scrape targets and remote_write for debugging
echo "Configured scrape targets:"
grep -E "targets:|scheme:" /etc/prometheus/prometheus.yml | head -20
echo ""
echo "Configured remote_write:"
grep -A 10 "^remote_write:" /etc/prometheus/prometheus.yml
echo ""
echo "Verifying placeholder substitutions:"
if grep -q "MIMIR_URL" /etc/prometheus/prometheus.yml; then
    echo "  ❌ ERROR: MIMIR_URL placeholder NOT replaced!"
else
    echo "  ✅ MIMIR_URL placeholder successfully replaced"
fi
if grep -q "ALERTMANAGER_TARGET" /etc/prometheus/prometheus.yml; then
    echo "  ❌ ERROR: ALERTMANAGER_TARGET placeholder NOT replaced!"
else
    echo "  ✅ ALERTMANAGER_TARGET placeholder successfully replaced"
fi
echo ""
echo "Configured alerting:"
grep -A 5 "^alerting:" /etc/prometheus/prometheus.yml || echo "  (no alerting section found)"
echo ""
echo "Configured rule_files:"
grep -A 5 "^rule_files:" /etc/prometheus/prometheus.yml || echo "  (no rule_files section found)"
echo ""
echo "Verifying rule files exist:"
if [ -f /etc/prometheus/alert.rules.yml ]; then
    ALERT_COUNT=$(grep -c "alert:" /etc/prometheus/alert.rules.yml 2>/dev/null || echo "0")
    echo "  ✅ alert.rules.yml exists ($ALERT_COUNT alert rules)"
else
    echo "  ❌ alert.rules.yml NOT FOUND!"
fi
if [ -f /etc/prometheus/recording_rules_baselines.yml ]; then
    RECORD_COUNT=$(grep -c "record:" /etc/prometheus/recording_rules_baselines.yml 2>/dev/null || echo "0")
    echo "  ✅ recording_rules_baselines.yml exists ($RECORD_COUNT recording rules)"
else
    echo "  ❌ recording_rules_baselines.yml NOT FOUND!"
fi
echo ""
echo "Validating Prometheus configuration..."
if promtool check config /etc/prometheus/prometheus.yml 2>/dev/null; then
    echo "  ✅ Configuration is valid"
else
    echo "  ⚠️  Configuration validation skipped or failed (promtool may not be available)"
fi
echo "==========================================="

# Start Prometheus with provided arguments
exec prometheus "$@"
