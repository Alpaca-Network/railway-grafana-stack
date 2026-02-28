ARG VERSION=v0.27.0

FROM prom/alertmanager:${VERSION}

# Run as root for Railway volume permissions
USER root

# Create data directory
RUN mkdir -p /data/alertmanager && chmod 0777 /data/alertmanager

# Copy configuration and entrypoint
COPY alertmanager.yml /etc/alertmanager/alertmanager.yml
COPY entrypoint.sh    /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose Alertmanager ports
# 9093 — HTTP API (alert ingestion from Prometheus, UI, silence management)
EXPOSE 9093

ENTRYPOINT ["/entrypoint.sh"]
CMD [ \
  "--config.file=/etc/alertmanager/alertmanager.yml", \
  "--storage.path=/data/alertmanager", \
  "--log.level=info" \
]
