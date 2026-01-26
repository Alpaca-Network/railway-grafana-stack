# Pin to specific version for stability
FROM grafana/tempo:2.6.1

# Run as root for Railway volume permissions
USER root

# Create data directories
RUN mkdir -p /var/tempo/traces /var/tempo/wal && chmod -R 777 /var/tempo

COPY tempo.yml /etc/tempo/tempo.yml

# Expose Tempo ports for Railway private networking
# 3200 - HTTP API (Grafana queries)
# 4317 - OTLP gRPC (trace ingestion)
# 4318 - OTLP HTTP (trace ingestion)
EXPOSE 3200 4317 4318

CMD ["-config.file=/etc/tempo/tempo.yml"]
