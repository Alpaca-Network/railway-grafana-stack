#!/bin/bash
set -e

# Determine if running on Railway or locally
if [ -z "$RAILWAY_ENVIRONMENT" ]; then
    # Local Docker Compose environment
    FASTAPI_TARGET="fastapi_app:8000"
else
    # Railway production environment
    FASTAPI_TARGET="fastapi-app.railway.internal:8000"
fi

# Create a temporary config file with the correct target
cp /etc/prometheus/prom.yml /tmp/prom.yml.tmp
sed "s|FASTAPI_TARGET|${FASTAPI_TARGET}|g" /tmp/prom.yml.tmp > /etc/prometheus/prom.yml

# Start Prometheus
exec prometheus "$@"
