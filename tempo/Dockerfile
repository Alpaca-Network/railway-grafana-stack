ARG VERSION=latest

FROM grafana/tempo:${VERSION}

# Run as root for Railway volume permissions
USER root

COPY tempo.yml /etc/tempo/tempo.yml

CMD ["-config.file=/etc/tempo/tempo.yml"]