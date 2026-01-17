FROM grafana/mimir:2.11.0

# Copy both configurations (Railway and local)
COPY mimir.yml /etc/mimir/mimir.yml
COPY mimir-railway.yml /etc/mimir/mimir-railway.yml

# Create data directories
USER root
RUN mkdir -p /data/mimir/blocks /data/mimir/tsdb /data/mimir/bucket-sync /data/mimir/compactor && \
    chown -R mimir:mimir /data/mimir

USER mimir

# Expose ports
# 9009 - HTTP API
# 9095 - gRPC
# 7946 - Memberlist
EXPOSE 9009 9095 7946

# Health check - longer start period for Railway
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD wget -qO- http://localhost:9009/ready || exit 1

# Run Mimir with Railway config by default, fallback to regular config
# Can override with CONFIG_FILE env var
ENTRYPOINT ["/bin/sh", "-c"]
CMD ["exec /bin/mimir -config.file=${CONFIG_FILE:-/etc/mimir/mimir-railway.yml}"]
