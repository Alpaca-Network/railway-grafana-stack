#!/bin/sh
set -e

echo "=== Tempo Startup ==="

# Check for corrupted WAL files (invalid UUID errors)
# WAL files should have valid UUIDs as directory names
if [ -d "/var/tempo/wal" ]; then
    echo "Checking WAL directory for corruption..."
    
    # Find any files/dirs that don't match UUID pattern (8-4-4-4-12 hex chars)
    # Valid UUID example: 550e8400-e29b-41d4-a716-446655440000
    CORRUPTED=$(find /var/tempo/wal -maxdepth 1 -type d ! -name "wal" 2>/dev/null | while read dir; do
        basename "$dir" | grep -vE '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' && echo "$dir"
    done || true)
    
    if [ -n "$CORRUPTED" ] || [ "$(find /var/tempo/wal -type f -name "*.tmp" 2>/dev/null | wc -l)" -gt 0 ]; then
        echo "WARNING: Found potentially corrupted WAL data. Clearing WAL directory..."
        rm -rf /var/tempo/wal/*
        echo "WAL directory cleared."
    else
        echo "WAL directory looks healthy."
    fi
fi

# Ensure directories exist with correct permissions
mkdir -p /var/tempo/traces /var/tempo/wal
chmod -R 777 /var/tempo

echo "Starting Tempo..."
exec /tempo -config.file=/etc/tempo/tempo.yml "$@"
