ARG VERSION=v3.2.1

FROM prom/prometheus:${VERSION}

# Run as root for Railway volume permissions
USER root

# Copy the prom.yml configuration file to the container
COPY prom.yml /etc/prometheus/prom.yml

# Expose Prometheus port for Railway private networking
EXPOSE 9090

# Command to run Prometheus
CMD ["--config.file=/etc/prometheus/prom.yml", "--storage.tsdb.path=/prometheus"]