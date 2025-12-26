ARG VERSION=latest

FROM grafana/tempo:${VERSION}

# Run as root for Railway volume permissions
USER root

COPY tempo.yml /etc/tempo/tempo.yml

# Expose Tempo ports for Railway private networking
EXPOSE 3200
EXPOSE 4317
EXPOSE 4318

CMD ["-config.file=/etc/tempo/tempo.yml"]