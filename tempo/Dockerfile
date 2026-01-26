# Pin to specific version for stability
FROM grafana/tempo:2.6.1

# Run as root for Railway volume permissions
USER root

# Create data directories
RUN mkdir -p /var/tempo/traces /var/tempo/wal && chmod -R 777 /var/tempo

COPY tempo.yml /etc/tempo/tempo.yml

# PORT CONFIGURATION FOR RAILWAY:
# Tempo listens on multiple ports (configured in tempo.yml):
#   - 3200: HTTP API (Grafana queries, health checks)
#   - 4317: OTLP gRPC (trace ingestion)
#   - 4318: OTLP HTTP (trace ingestion)
#
# Railway exposes port 3200 publicly for Grafana queries
# Backend uses internal DNS (tempo.railway.internal:4318) for trace ingestion
EXPOSE 3200

CMD ["-config.file=/etc/tempo/tempo.yml"]
