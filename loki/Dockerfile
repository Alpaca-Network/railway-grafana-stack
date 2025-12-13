ARG VERSION=3.4

FROM grafana/loki:${VERSION}

# Run as root for Railway volume permissions
USER root

# Copy the loki.yml configuration file to the default path expected by the image
COPY loki.yml /etc/loki/config.yaml

# Expose Loki port for Railway private networking
EXPOSE 3100

# The base image entrypoint already runs Loki with /etc/loki/config.yaml, so no CMD needed.