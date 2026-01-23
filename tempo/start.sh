#!/bin/sh
set -e

echo "Starting Tempo..."
echo "Config file: /etc/tempo/tempo.yml"
echo "Creating storage directories..."

# Create storage directories with proper permissions
mkdir -p /tmp/tempo/traces
mkdir -p /tmp/tempo/wal
chmod -R 777 /tmp/tempo

echo "Storage directories created"
echo "Starting Tempo process..."

# Start Tempo with explicit configuration
exec tempo -config.file=/etc/tempo/tempo.yml -target=all
