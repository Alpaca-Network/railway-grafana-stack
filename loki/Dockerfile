ARG VERSION=3.4

FROM grafana/loki:${VERSION}

# Run as root for Railway volume permissions
USER root

# Create data directories with open permissions
RUN mkdir -p /loki/chunks /loki/index /loki/boltdb-shipper-active /loki/boltdb-shipper-cache \
    /loki/rules/fake /loki/ruler-wal \
    && chmod -R 0777 /loki

# Copy the loki.yml configuration file to the container
COPY loki.yml /etc/loki/loki-config.yaml

# Copy recording rules to a staging location
# entrypoint.sh will copy them to /loki/rules/fake/ at runtime
COPY rules/ /etc/loki/rules/

# Copy and make entrypoint executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose Loki port for Railway private networking
EXPOSE 3100

ENTRYPOINT ["/entrypoint.sh"]
