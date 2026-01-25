FROM oliver006/redis_exporter:v1.66.0

# Run as root for Railway
USER root

# Expose metrics port
EXPOSE 9121

# ============================================================
# Redis Exporter Configuration
# ============================================================
# The redis exporter reads configuration from environment variables.
# Set these in Railway:
#
# Required:
#   REDIS_ADDR=redis-production-bb6d.up.railway.app:6379
#   REDIS_PASSWORD=your-redis-password
#
# Optional:
#   REDIS_EXPORTER_WEB_LISTEN_ADDRESS=:9121 (default)
#   REDIS_EXPORTER_DEBUG=false
#
# The exporter will connect to Redis and expose metrics at /metrics
# ============================================================

# Start redis_exporter
ENTRYPOINT ["/redis_exporter"]
