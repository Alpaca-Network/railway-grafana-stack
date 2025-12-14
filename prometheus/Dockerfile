ARG VERSION=v3.2.1

FROM prom/prometheus:${VERSION}

# Run as root for Railway volume permissions
USER root

# Copy the prom.yml configuration file to the container
COPY prom.yml /etc/prometheus/prom.yml

# Copy alert rules
COPY alert.rules.yml /etc/prometheus/alert.rules.yml

# Copy entrypoint script for environment-aware config
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose Prometheus port for Railway private networking
EXPOSE 9090

# Use entrypoint script to substitute config based on environment
ENTRYPOINT ["/entrypoint.sh"]
CMD ["--config.file=/etc/prometheus/prom.yml", "--storage.tsdb.path=/prometheus"]