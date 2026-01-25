ARG VERSION=v0.27.0

FROM prom/alertmanager:${VERSION}

# Run as root for Railway volume permissions
USER root

# Create data directory for alertmanager storage
RUN mkdir -p /alertmanager && chmod 0777 /alertmanager

# Copy configuration
COPY alertmanager.yml /etc/alertmanager/alertmanager.yml

# Copy entrypoint script for environment variable substitution
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose Alertmanager ports
# 9093 - HTTP API and web UI
# 9094 - Cluster communication (for HA setup)
EXPOSE 9093 9094

# Use entrypoint script to substitute environment variables
ENTRYPOINT ["/entrypoint.sh"]
CMD ["--config.file=/etc/alertmanager/alertmanager.yml", \
     "--storage.path=/alertmanager", \
     "--web.listen-address=:9093", \
     "--cluster.listen-address="]
