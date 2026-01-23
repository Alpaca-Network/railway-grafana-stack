ARG VERSION=latest

FROM grafana/tempo:${VERSION}

# Run as root for Railway volume permissions
USER root

# Copy configuration and startup script
COPY tempo.yml /etc/tempo/tempo.yml
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Create storage directories
RUN mkdir -p /tmp/tempo/traces /tmp/tempo/wal && \
    chmod -R 777 /tmp/tempo

# Expose Tempo ports for Railway private networking
EXPOSE 3200
EXPOSE 3201
EXPOSE 4317
EXPOSE 4318

# Use startup script
CMD ["/start.sh"]
