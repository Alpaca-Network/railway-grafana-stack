FROM grafana/mimir:2.11.0

# Run as root for Railway volume compatibility (like prometheus, loki)
USER root

# Copy configurations
COPY mimir.yml /etc/mimir/mimir.yml
COPY mimir-railway.yml /etc/mimir/mimir-railway.yml

# Copy and make entrypoint executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create all required data directories with open permissions
RUN mkdir -p \
    /data/mimir/blocks \
    /data/mimir/tsdb \
    /data/mimir/bucket-sync \
    /data/mimir/compactor \
    /data/mimir/rules \
    && chmod -R 0777 /data/mimir

# Set working directory
WORKDIR /data/mimir

# Expose ports
# 9009 - HTTP API (Railway uses this)
# 9095 - gRPC
# 7946 - Memberlist
EXPOSE 9009 9095 7946

# Health check - longer start period for Railway
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD wget -qO- http://localhost:9009/ready || exit 1

# Run Mimir via entrypoint script
ENTRYPOINT ["/entrypoint.sh"]
