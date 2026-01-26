# Pin to specific version for stability
FROM grafana/tempo:2.6.1

# Run as root for Railway volume permissions
USER root

# Create data directories
RUN mkdir -p /var/tempo/traces /var/tempo/wal /var/tempo/generator/wal && chmod -R 777 /var/tempo

COPY tempo.yml /etc/tempo/tempo.yml

# PORT CONFIGURATION FOR RAILWAY:
# Tempo listens on multiple ports (configured in tempo.yml):
#   - 3200: HTTP API (Grafana queries, health checks) - PUBLIC
#   - 4317: OTLP gRPC (trace ingestion) - INTERNAL
#   - 4318: OTLP HTTP (trace ingestion) - INTERNAL
#
# IMPORTANT: All ports must be exposed for Railway internal networking
# Railway will expose port 3200 publicly (configured in Railway settings)
# Backend uses internal DNS (tempo.railway.internal:4318) for trace ingestion
EXPOSE 3200 4317 4318

CMD ["-config.file=/etc/tempo/tempo.yml"]
