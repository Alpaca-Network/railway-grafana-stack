ARG VERSION=v3.2.1

FROM prom/prometheus:${VERSION}

# Run as root for Railway volume permissions
USER root

# Ensure the TSDB directory and secrets directory are writable
RUN mkdir -p /prometheus /etc/prometheus/secrets \
  && chmod 0777 /prometheus /etc/prometheus/secrets

# Copy the prom.yml configuration file to the container
COPY prom.yml /etc/prometheus/prom.yml

# Copy alert rules
COPY alert.rules.yml /etc/prometheus/alert.rules.yml

# Copy recording rules for baseline calculations (used by anomaly detection alerts)
COPY recording_rules_baselines.yml /etc/prometheus/recording_rules_baselines.yml

# Copy and make entrypoint executable (handles FASTAPI_TARGET substitution)
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy diagnostic scripts (for troubleshooting Prometheus → Mimir connection)
COPY diagnose-prometheus-mimir.sh /app/diagnose-prometheus-mimir.sh
COPY verify-remote-write.sh /app/verify-remote-write.sh
RUN chmod +x /app/diagnose-prometheus-mimir.sh /app/verify-remote-write.sh

# Expose Prometheus port for Railway private networking
EXPOSE 9090

# Use entrypoint script to substitute environment variables, then start Prometheus
ENTRYPOINT ["/entrypoint.sh"]
CMD ["--config.file=/etc/prometheus/prom.yml", "--storage.tsdb.path=/prometheus"]
