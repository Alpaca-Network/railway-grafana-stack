#!/bin/sh
set -e

# ============================================================
# Alertmanager Entrypoint Script
# Substitutes environment-specific values in alertmanager.yml:
# - SMTP_USERNAME, SMTP_PASSWORD (email credentials)
# - GRAFANA_URL (dashboard links in alerts)
# ============================================================

echo "==========================================="
echo "Alertmanager Configuration"
echo "==========================================="

# ============================================================
# Grafana URL Configuration
# Determines Grafana URL based on environment
# ============================================================

if [ -n "$GRAFANA_EXTERNAL_URL" ]; then
    # Use explicitly set Grafana URL
    GRAFANA_URL="$GRAFANA_EXTERNAL_URL"
elif [ -n "$RAILWAY_ENVIRONMENT" ]; then
    # Railway production - use public Grafana URL
    # This should be set as environment variable in Railway
    GRAFANA_URL="${GRAFANA_URL:-https://logs.gatewayz.ai}"
else
    # Local Docker Compose
    GRAFANA_URL="http://localhost:3000"
fi

echo "GRAFANA_URL: $GRAFANA_URL"
echo "SMTP_USERNAME: ${SMTP_USERNAME:-(not set)}"
echo "SMTP_PASSWORD: ${SMTP_PASSWORD:+(set but hidden)}"
echo "RAILWAY_ENVIRONMENT: ${RAILWAY_ENVIRONMENT:-not set (local mode)}"
echo "==========================================="

# Substitute environment variables in alertmanager.yml
# Using envsubst for proper variable substitution
cp /etc/alertmanager/alertmanager.yml /tmp/alertmanager.yml.tmp

# Export variables for envsubst
export GRAFANA_URL
export SMTP_USERNAME="${SMTP_USERNAME:-}"
export SMTP_PASSWORD="${SMTP_PASSWORD:-}"

# Replace localhost:3000 with actual Grafana URL
sed -e "s|http://localhost:3000|${GRAFANA_URL}|g" \
    -e "s|\${SMTP_USERNAME}|${SMTP_USERNAME}|g" \
    -e "s|\${SMTP_PASSWORD}|${SMTP_PASSWORD}|g" \
    /tmp/alertmanager.yml.tmp > /etc/alertmanager/alertmanager.yml

echo "Configuration substitution complete."
echo ""

# Validate config if amtool is available
if command -v amtool > /dev/null 2>&1; then
    echo "Validating alertmanager configuration..."
    if amtool check-config /etc/alertmanager/alertmanager.yml; then
        echo "✅ Configuration is valid"
    else
        echo "❌ Configuration validation failed!"
        exit 1
    fi
fi

echo "==========================================="
echo "Starting Alertmanager..."
echo "==========================================="

# Start Alertmanager with provided arguments
exec alertmanager "$@"
