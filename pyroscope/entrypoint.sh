#!/bin/sh
set -e

echo "=== Pyroscope Startup ==="
echo "Environment: ${RAILWAY_ENVIRONMENT:-local}"
echo "Data directory: /data/pyroscope"

# Ensure the data directory exists with correct permissions
mkdir -p /data/pyroscope
chmod -R 777 /data/pyroscope || true

echo "Starting Pyroscope on port 4040..."
exec /usr/bin/pyroscope -config.file=/etc/pyroscope/pyroscope.yml "$@"
