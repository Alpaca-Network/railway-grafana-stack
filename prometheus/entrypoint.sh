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

    # Strip scheme prefix if accidentally included (Prometheus targets must be host:port only)
    TARGET=$(echo "$TARGET" | sed 's|^https://||' | sed 's|^http://||')

    # Auto-detect scheme based on target
    case "$TARGET" in
        api.gatewayz.ai*|*.railway.app*|*.up.railway.app*)
            SCHEME="${FASTAPI_SCHEME:-https}"
            ;;
        *.railway.internal*)
            # Railway internal networking — always plain HTTP
            SCHEME="${FASTAPI_SCHEME:-http}"
            # Append default port if not specified
            case "$TARGET" in
                *:*) ;; # already has port
                *) TARGET="${TARGET}:8000" ;;
            esac
            ;;
        *)
            SCHEME="${FASTAPI_SCHEME:-http}"
            ;;
    esac
elif [ -n "$RAILWAY_ENVIRONMENT" ]; then
    # Railway production environment - use internal network
    # Service name: gatewayz-backend (see docs/development/CLAUDE.md)
    TARGET="gatewayz-backend.railway.internal:8000"
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
# Alertmanager Configuration (OPTIONAL)
# Alertmanager is disabled by default. Grafana Alerting is used instead.
# To enable, set ALERTMANAGER_INTERNAL_URL and uncomment in prometheus.yml
# ============================================================

if [ -n "$ALERTMANAGER_INTERNAL_URL" ]; then
    ALERTMANAGER_TARGET=$(echo "$ALERTMANAGER_INTERNAL_URL" | sed 's|http://||')
    echo "Alertmanager enabled: $ALERTMANAGER_TARGET"
else
    ALERTMANAGER_TARGET="alertmanager:9093"
    echo "Alertmanager disabled (using Grafana Alerting instead)"
fi

# ============================================================
# Redis Exporter Configuration
# Redis Exporter runs as a service in this stack (local or Railway)
# It connects to REDIS_ADDR defined in environment variables
# ============================================================


# ============================================================
# Tempo Configuration
# Tempo metrics endpoint for span metrics (model popularity, etc.)
# ============================================================

if [ -n "$TEMPO_INTERNAL_URL" ]; then
    # Use explicitly set TEMPO_INTERNAL_URL (from Railway env vars)
    TEMPO_TARGET=$(echo "$TEMPO_INTERNAL_URL" | sed 's|http://||')
elif [ -n "$RAILWAY_ENVIRONMENT" ]; then
    # Railway production environment - use internal network
    TEMPO_TARGET="tempo.railway.internal:3200"
else
    # Local Docker Compose environment - use Docker service name
    TEMPO_TARGET="tempo:3200"
fi

echo "==========================================="
echo "Prometheus Configuration"
echo "==========================================="
echo "FASTAPI_TARGET: $TARGET"
echo "FASTAPI_SCHEME: $SCHEME"
echo "MIMIR_URL: $MIMIR_URL"
echo "MIMIR_TARGET: $MIMIR_TARGET"
echo "ALERTMANAGER_TARGET: $ALERTMANAGER_TARGET"

echo "TEMPO_TARGET: $TEMPO_TARGET"
echo "RAILWAY_ENVIRONMENT: ${RAILWAY_ENVIRONMENT:-not set (local mode)}"
echo "==========================================="

# ============================================================
# Bearer Token for Backend Scraping
# Write the PRODUCTION_BEARER_TOKEN env var to a file so
# Prometheus can use bearer_token_file in scrape configs
# ============================================================
# Quick connectivity test to the backend
echo ""
echo "Testing backend connectivity..."
BACKEND_URL="${SCHEME}://${TARGET}/metrics"
echo "  Target URL: $BACKEND_URL"
if wget -qO- --timeout=5 "$BACKEND_URL" 2>/dev/null | head -1 | grep -q "#"; then
    echo "  ✅ Backend /metrics is reachable"
else
    echo "  ⚠️  Backend /metrics not reachable at $BACKEND_URL (may start later)"
fi
echo ""

if [ -n "$PRODUCTION_BEARER_TOKEN" ]; then
    echo "$PRODUCTION_BEARER_TOKEN" > /etc/prometheus/secrets/production_bearer_token
    chmod 600 /etc/prometheus/secrets/production_bearer_token
    echo "  ✅ Bearer token written to /etc/prometheus/secrets/production_bearer_token"
else
    # Prometheus refuses to scrape targets with bearer_token_file pointing to a
    # missing file. Write an empty file so the scrape config still works (the
    # backend /metrics endpoint does not require auth).
    touch /etc/prometheus/secrets/production_bearer_token
    chmod 600 /etc/prometheus/secrets/production_bearer_token
    echo "  ⚠️  PRODUCTION_BEARER_TOKEN not set — wrote empty token file (backend /metrics is unauthenticated)"
fi

# Substitute placeholders in prometheus.yml
cp /etc/prometheus/prometheus.yml /tmp/prometheus.yml.tmp
sed -e "s|FASTAPI_TARGET|${TARGET}|g" \
    -e "s|FASTAPI_SCHEME|${SCHEME}|g" \
    -e "s|MIMIR_URL|${MIMIR_URL}|g" \
    -e "s|MIMIR_TARGET|${MIMIR_TARGET}|g" \
    -e "s|ALERTMANAGER_TARGET|${ALERTMANAGER_TARGET}|g" \
    -e "s|TEMPO_TARGET|${TEMPO_TARGET}|g" \
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
# Alertmanager is optional - only check if enabled
if grep -q "^alerting:" /etc/prometheus/prometheus.yml; then
    if grep -q "ALERTMANAGER_TARGET" /etc/prometheus/prometheus.yml; then
        echo "  ⚠️  ALERTMANAGER_TARGET placeholder not replaced (Alertmanager may not be configured)"
    else
        echo "  ✅ Alertmanager configured"
    fi
else
    echo "  ℹ️  Alertmanager disabled (using Grafana Alerting)"
fi
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
echo ""
echo "Testing Mimir connectivity..."
# Wait for Mimir to be ready (important for remote_write)
MIMIR_READY=false
for i in 1 2 3 4 5; do
    if wget -qO- "${MIMIR_URL}/ready" 2>/dev/null | grep -q "ready"; then
        echo "  ✅ Mimir is ready at ${MIMIR_URL}"
        MIMIR_READY=true
        break
    fi
    echo "  ⏳ Waiting for Mimir to be ready (attempt $i/5)..."
    sleep 2
done
if [ "$MIMIR_READY" = "false" ]; then
    echo "  ⚠️  Mimir not ready yet. Remote write will retry automatically."
    echo "     Check Mimir logs if this persists."
fi
# ============================================================
# Start Redis Exporter Sidecar
# ============================================================
if [ -n "$REDIS_ADDR" ]; then
    echo "Starting redis_exporter sidecar..."
    echo "  Redis Address: $REDIS_ADDR"
    
    # Remove protocol prefix for connectivity check
    REDIS_HOST=$(echo "$REDIS_ADDR" | sed 's|^redis://||' | sed 's|^rediss://||' | cut -d: -f1)
    REDIS_PORT=$(echo "$REDIS_ADDR" | sed 's|^redis://||' | sed 's|^rediss://||' | cut -d: -f2)
    
    echo "  Checking connectivity to ${REDIS_HOST}:${REDIS_PORT}..."
    if nc -z -w 5 "$REDIS_HOST" "$REDIS_PORT" 2>/dev/null; then
        echo "  ✅ TCP connection successful"
    else
        echo "  ⚠️  TCP connection check failed (nc not available or unreachable)"
    fi

    # Run with debug logging to help diagnose connection issues
    # Explicitly pass address and password to avoid environment variable ambiguity
    # Pass -skip-tls-verification in case TLS is auto-detected
    CMD_ARGS="-redis.addr=$REDIS_ADDR -redis.password=$REDIS_PASSWORD -debug -log-format=json -skip-tls-verification"
    
    if [ -n "$REDIS_USER" ]; then
        echo "  Using Redis User: $REDIS_USER"
        CMD_ARGS="$CMD_ARGS -redis.user=$REDIS_USER"
    fi

    /usr/local/bin/redis_exporter $CMD_ARGS &
        
    EXPORTER_PID=$!
    echo "  ✅ redis_exporter started (pid $EXPORTER_PID)"

    # Wait a moment and check if it's still running
    sleep 3
    if kill -0 $EXPORTER_PID 2>/dev/null; then
         echo "  ✅ redis_exporter is running"
         # Optional: Try to scrape metrics to verify connection (requires wget)
         if wget -qO- http://localhost:9121/metrics | grep -q "redis_up"; then
             echo "  ✅ redis_exporter is serving metrics"
             # Check if redis_up is actually 1
             if wget -qO- http://localhost:9121/metrics | grep "redis_up 1"; then
                 echo "  ✅ Connected to Redis successfully (redis_up=1)"
             else
                 echo "  ❌ Connected to Redis FAILED (redis_up=0). Check logs!"
             fi
         else
             echo "  ⚠️  redis_exporter is running but metrics check failed (might be starting up)"
         fi
    else
         echo "  ❌ redis_exporter crashed! Check logs above."
    fi
else
    echo "  ℹ️  REDIS_ADDR not set, skipping redis_exporter sidecar"
fi

echo "==========================================="

# Start Prometheus with provided arguments
exec prometheus "$@"
