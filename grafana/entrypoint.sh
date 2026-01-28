#!/bin/sh
set -e

# Clean up Grafana database cache on startup to ensure fresh dashboard state
# This removes any cached folder structures from previous runs
echo "Cleaning up Grafana database cache..."
rm -rf /var/lib/grafana/grafana.db \
       /var/lib/grafana/sessions \
       2>/dev/null || true

echo "Starting Grafana..."
# Execute the original Grafana entrypoint
exec /run.sh "$@"
