FROM grafana/mimir:2.11.0

# Copy Mimir configuration
COPY mimir.yml /etc/mimir/mimir.yml

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

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget -qO- http://localhost:9009/ready || exit 1

# Run Mimir
ENTRYPOINT ["/bin/mimir"]
CMD ["-config.file=/etc/mimir/mimir.yml"]
