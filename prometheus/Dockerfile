ARG VERSION=v3.2.1

FROM prom/prometheus:${VERSION}

# Run as root for Railway volume permissions
USER root

# Ensure the TSDB directory is writable even if the attached volume is owned by a
# different UID/GID (common on some platforms / re-used volumes).
RUN mkdir -p /prometheus \
  && chmod 0777 /prometheus

# Copy the prom.yml configuration file to the container
COPY prom.yml /etc/prometheus/prom.yml

# Copy alert rules
COPY alert.rules.yml /etc/prometheus/alert.rules.yml

# Expose Prometheus port for Railway private networking
EXPOSE 9090

# Command to run Prometheus
CMD ["--config.file=/etc/prometheus/prom.yml", "--storage.tsdb.path=/prometheus"]
