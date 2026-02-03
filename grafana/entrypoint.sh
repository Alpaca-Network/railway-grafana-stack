#!/bin/sh
set -e

# ============================================================
# Grafana Entrypoint Script
# Generates grafana.ini with SMTP configuration from env vars
# ============================================================

echo "==========================================="
echo "Grafana Configuration"
echo "==========================================="

# Generate grafana.ini from environment variables
cat > /etc/grafana/grafana.ini << EOF
# Grafana Configuration - Generated at runtime

[smtp]
enabled = true
host = smtp.gmail.com:587
user = ${GF_SMTP_USER:-}
password = ${GF_SMTP_PASSWORD:-}
from_address = ${GF_SMTP_FROM_ADDRESS:-grafana@localhost}
from_name = ${GF_SMTP_FROM_NAME:-Grafana}
startTLS_policy = MandatoryStartTLS

[alerting]
enabled = true
execute_alerts = true

[unified_alerting]
enabled = true
EOF

# Verify SMTP configuration
if [ -n "$GF_SMTP_USER" ] && [ -n "$GF_SMTP_PASSWORD" ]; then
    echo "  SMTP User: $GF_SMTP_USER"
    echo "  SMTP From: ${GF_SMTP_FROM_ADDRESS:-grafana@localhost}"
    echo "  SMTP configured successfully"
else
    echo "  WARNING: SMTP credentials not set"
    echo "  Set GF_SMTP_USER and GF_SMTP_PASSWORD environment variables"
fi

echo "==========================================="

# Start Grafana
exec /run.sh "$@"
