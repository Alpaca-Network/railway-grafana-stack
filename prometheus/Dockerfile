ARG VERSION=v3.2.1

FROM prom/prometheus:${VERSION}

# Run as root for Railway volume permissions
USER root

# Copy the prom.yml configuration file to the container
COPY prom.yml /etc/prometheus/prom.yml

# Copy alert rules
COPY alert.rules.yml /etc/prometheus/alert.rules.yml

# Expose Prometheus port for Railway private networking
EXPOSE 9090

# Command to run Prometheus (binary provided by base image entrypoint)
CMD ["--config.file=/etc/prometheus/prom.yml", "--storage.tsdb.path=/prometheus"]