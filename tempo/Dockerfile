# Pin to specific version for stability
FROM grafana/tempo:2.6.1

# Run as root for Railway volume permissions
USER root

# Create data directories
RUN mkdir -p /var/tempo/traces /var/tempo/wal && chmod -R 777 /var/tempo

COPY tempo.yml /etc/tempo/tempo.yml

# PORT CONFIGURATION FOR RAILWAY:
# - Railway exposes ONE port publicly (the first EXPOSE or PORT env var)
# - Port 3200 = HTTP API for Grafana queries (MUST be public for cross-project access)
# - Ports 4317/4318 = OTLP ingestion (accessible via railway.internal DNS from same project)
#
# Backend uses internal DNS: http://tempo.railway.internal:4318
# Grafana uses public URL: https://tempo-xxx.up.railway.app (routes to 3200)

# Only expose 3200 publicly - this is what Railway will route the public URL to
EXPOSE 3200

# Internal ports (accessible via railway.internal DNS, not public)
# 4317 - OTLP gRPC
# 4318 - OTLP HTTP

# Set PORT environment variable to explicitly tell Railway which port to use
ENV PORT=3200

CMD ["-config.file=/etc/tempo/tempo.yml"]
