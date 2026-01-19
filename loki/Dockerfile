ARG VERSION=3.4

FROM grafana/loki:${VERSION}

# Run as root for Railway volume permissions
USER root

# Create data directories with open permissions
RUN mkdir -p /loki/chunks /loki/index /loki/boltdb-shipper-active /loki/boltdb-shipper-cache \
    && chmod -R 0777 /loki

# Copy the loki.yml configuration file to the container
COPY loki.yml /etc/loki/loki-config.yaml

# Expose Loki port for Railway private networking
EXPOSE 3100

# Command to run Loki
CMD ["-config.file=/etc/loki/loki-config.yaml"]